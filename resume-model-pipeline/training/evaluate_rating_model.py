"""Evaluate the trained rating model on the validation and test sets, beside a majority-class baseline.

  python training/evaluate_rating_model.py --model-s3 s3://<bucket>/rating-model/output/<job>/output/model.tar.gz

Downloads and unpacks the model into models/<job>/, rates every resume on CPU, and writes
  reports/model_evaluation.json        per split and criterion: QWK, macro-F1, exact, per-level scores, confusion matrix, baseline
  reports/model_predictions.csv        gold and predicted levels per resume, for error analysis
"""

import argparse
import json
import sys
import tarfile
from pathlib import Path

import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rating_metrics import LEVELS, criterion_metrics, majority_baseline  # noqa: E402
from rating_model import CRITERIA, chunk_resume, load_model  # noqa: E402


def fetch_model(s3_uri, profile, region, models_dir="models"):
    """Download model.tar.gz from S3 and unpack it into models/<job name>/."""
    import boto3
    bucket, key = s3_uri.removeprefix("s3://").split("/", 1)
    job = key.split("/")[-3]  # .../output/<job>/output/model.tar.gz
    dest = Path(models_dir) / job
    if not (dest / "rating_model.pt").exists():
        dest.mkdir(parents=True, exist_ok=True)
        tar_path = dest / "model.tar.gz"
        print(f"Downloading {s3_uri}")
        boto3.Session(profile_name=profile, region_name=region).client("s3").download_file(bucket, key, str(tar_path))
        with tarfile.open(tar_path) as tar:
            tar.extractall(dest, filter="data")
        tar_path.unlink()
    return dest


def predict(model, tokenizer, texts, max_chunks):
    preds = []
    with torch.no_grad():
        for i, text in enumerate(texts, 1):
            ids, att = chunk_resume(tokenizer, text, max_chunks)
            logits = model(torch.tensor([ids]), torch.tensor([att]), torch.ones(1, len(ids), dtype=torch.long))
            preds.append(logits.argmax(dim=-1)[0].tolist())
            if i % 50 == 0:
                print(f"  {i}/{len(texts)}")
    return preds


def per_level(gold, pred):
    """Precision, recall and F1 for each level, so rare levels are visible."""
    out = {}
    for lv in LEVELS:
        tp = sum(g == lv and p == lv for g, p in zip(gold, pred))
        n_gold, n_pred = gold.count(lv), pred.count(lv)
        precision = tp / n_pred if n_pred else None
        recall = tp / n_gold if n_gold else None
        f1 = 2 * tp / (n_gold + n_pred) if (n_gold + n_pred) else None
        out[lv] = {"gold": n_gold, "predicted": n_pred,
                   **{k: None if v is None else round(v, 3) for k, v in [("precision", precision), ("recall", recall), ("f1", f1)]}}
    return out


def confusion(gold, pred):
    m = [[0] * len(LEVELS) for _ in LEVELS]
    for g, p in zip(gold, pred):
        m[g][p] += 1
    return m


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--model-s3", help="S3 URI of model.tar.gz from the training job")
    src.add_argument("--model-dir", help="Folder that already holds the unpacked model")
    p.add_argument("--profile", default="kerjaready")
    p.add_argument("--region", default="ap-southeast-5")
    p.add_argument("--splits-dir", default="data/splits")
    p.add_argument("--out", default="reports/model_evaluation")
    args = p.parse_args(argv)

    model_dir = fetch_model(args.model_s3, args.profile, args.region) if args.model_s3 else Path(args.model_dir)
    config = json.loads((model_dir / "rating_config.json").read_text(encoding="utf-8"))
    model, tokenizer = load_model(model_dir)
    splits = {n: pd.read_csv(Path(args.splits_dir) / f"{n}.csv", dtype={"resume_id": str}) for n in ["train", "val", "test"]}

    report = {"model_dir": str(model_dir), "best_epoch": config.get("best_epoch"), "checkpoint": config.get("checkpoint"),
              "max_chunks": config["max_chunks"], "splits": {}}
    rows = []
    for name in ["val", "test"]:
        d = splits[name]
        print(f"Rating {len(d)} {name} resumes")
        preds = predict(model, tokenizer, d["text"].fillna("").tolist(), config["max_chunks"])
        report["splits"][name] = {}
        for j, c in enumerate(CRITERIA):
            gold, pred = d[c].astype(int).tolist(), [p_[j] for p_ in preds]
            report["splits"][name][c] = {
                "model": criterion_metrics(gold, pred),
                "baseline": majority_baseline(splits["train"][c].astype(int).tolist(), gold),
                "per_level": per_level(gold, pred),
                "confusion_gold_rows_pred_cols": confusion(gold, pred),
            }
        for rid, g, pr in zip(d["resume_id"], d[CRITERIA].astype(int).values.tolist(), preds):
            rows.append({"split": name, "resume_id": rid, **{f"{c}_gold": g[j] for j, c in enumerate(CRITERIA)},
                         **{f"{c}_pred": pr[j] for j, c in enumerate(CRITERIA)}})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{out}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pred_path = out.parent / "model_predictions.csv"
    pd.DataFrame(rows).to_csv(pred_path, index=False)

    print(f"\nModel {model_dir} (best epoch {report['best_epoch']})")
    print(f"{'':6}{'':5}{'QWK':>7}{'F1':>7}{'exact':>7}   baseline F1   levels never predicted (gold count)")
    for name in ["val", "test"]:
        for c in CRITERIA:
            r = report["splits"][name][c]
            m, b = r["model"], r["baseline"]
            missed = [f"{lv}({v['gold']})" for lv, v in r["per_level"].items() if v["gold"] and not v["predicted"]]
            fmt = lambda v: "  n/a" if v is None else f"{v:.3f}"
            print(f"{name:6}{c.upper():5}{fmt(m['qwk']):>7}{fmt(m['macro_f1']):>7}{fmt(m['exact']):>7}   {fmt(b['macro_f1']):>11}   "
                  f"{', '.join(missed) or '-'}")
    print(f"\nWrote {out}.json and {pred_path}")


if __name__ == "__main__":
    main()