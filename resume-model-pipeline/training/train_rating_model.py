"""Fine-tune DistilBERT to rate A1, A2 and A3 (levels 0-3). Runs on your PC or as a SageMaker training job.

Local smoke test (a few resumes, CPU, about a minute or two):
  python training/train_rating_model.py --smoke

On SageMaker the train and val channels and the model folder come from the SM_* environment variables.
"""

import argparse
import json
import math
import os
import random
import time
from pathlib import Path

import pandas as pd
import torch
from torch import nn
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from transformers.utils import logging as hf_logging

from rating_metrics import criterion_metrics, majority_baseline
from rating_model import CHECKPOINT, CRITERIA, MAX_CHUNKS, NUM_LEVELS, ResumeRatingModel, chunk_resume, save_model

WEIGHT_CAP = 10.0


def channel_file(env_name, file_name, local_default):
    folder = os.environ.get(env_name)
    return str(Path(folder) / file_name) if folder else local_default


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train", default=channel_file("SM_CHANNEL_TRAIN", "train.csv", "data/splits/train.csv"))
    p.add_argument("--val", default=channel_file("SM_CHANNEL_VAL", "val.csv", "data/splits/val.csv"))
    p.add_argument("--model-dir", default=os.environ.get("SM_MODEL_DIR", "models/rating_model"))
    p.add_argument("--checkpoint", default=CHECKPOINT)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--patience", type=int, default=2, help="Stop after this many epochs without a better validation macro-F1")
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--grad-accum", type=int, default=4, help="Effective batch = batch size x this")
    p.add_argument("--lr", type=float, default=3e-5)
    p.add_argument("--warmup", type=float, default=0.1)
    p.add_argument("--max-chunks", type=int, default=MAX_CHUNKS)
    p.add_argument("--seed", type=int, default=200)
    p.add_argument("--limit-train", type=int, default=0)
    p.add_argument("--limit-val", type=int, default=0)
    p.add_argument("--smoke", action="store_true", help="Tiny run to check the code: 24 train, 12 val, 1 epoch, 2 chunks")
    args = p.parse_args(argv)
    if args.smoke:
        args.limit_train, args.limit_val, args.epochs, args.max_chunks = 24, 12, 1, 2
        args.batch_size, args.grad_accum = 2, 1
    return args


def load_split(path, limit, seed):
    d = pd.read_csv(path, dtype={"resume_id": str})
    if limit:
        d = d.sample(n=min(limit, len(d)), random_state=seed)
    labels = d[CRITERIA].astype(int).values.tolist()
    return d["text"].fillna("").tolist(), labels


def encode(tokenizer, texts, max_chunks):
    return [chunk_resume(tokenizer, t, max_chunks) for t in texts]


def class_weights(labels):
    """Square-root inverse-frequency weights per criterion, capped, so rare levels count more without exploding.

    A level with no training examples keeps weight 1; it never appears as a target, so it adds nothing to the loss.
    """
    weights = []
    n = len(labels)
    for j in range(len(CRITERIA)):
        counts = [sum(1 for row in labels if row[j] == lv) for lv in range(NUM_LEVELS)]
        present = sum(1 for c in counts if c)
        w = [min(WEIGHT_CAP, math.sqrt(n / (present * c))) if c else 1.0 for c in counts]
        weights.append(torch.tensor(w, dtype=torch.float))
    return weights


def batches(encoded, labels, batch_size, shuffle, rng):
    """Group resumes with similar chunk counts, so little padding is computed; shuffle batch order when training."""
    order = sorted(range(len(encoded)), key=lambda i: len(encoded[i][0]))
    groups = [order[i:i + batch_size] for i in range(0, len(order), batch_size)]
    if shuffle:
        rng.shuffle(groups)
    for g in groups:
        c = max(len(encoded[i][0]) for i in g)
        length = len(encoded[g[0]][0][0])
        ids = torch.zeros(len(g), c, length, dtype=torch.long)
        mask = torch.zeros(len(g), c, length, dtype=torch.long)
        chunk_mask = torch.zeros(len(g), c, dtype=torch.long)
        for row, i in enumerate(g):
            chunk_ids, chunk_att = encoded[i]
            k = len(chunk_ids)
            ids[row, :k] = torch.tensor(chunk_ids)
            mask[row, :k] = torch.tensor(chunk_att)
            chunk_mask[row, :k] = 1
        yield ids, mask, chunk_mask, torch.tensor([labels[i] for i in g], dtype=torch.long)


def evaluate(model, encoded, labels, device, batch_size):
    model.eval()
    preds = []
    gold = []
    with torch.no_grad():
        for ids, mask, chunk_mask, y in batches(encoded, labels, batch_size, False, None):
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(ids.to(device), mask.to(device), chunk_mask.to(device))
            preds += logits.argmax(dim=-1).cpu().tolist()
            gold += y.tolist()
    per = {c: criterion_metrics([g[j] for g in gold], [p[j] for p in preds]) for j, c in enumerate(CRITERIA)}
    f1s = [m["macro_f1"] for m in per.values() if m["macro_f1"] is not None]
    return per, (sum(f1s) / len(f1s) if f1s else 0.0)


def main(argv=None):
    args = parse_args(argv)
    hf_logging.set_verbosity_error()  # silences the "longer than 512 tokens" notice; resumes are chunked on purpose
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_texts, train_y = load_split(args.train, args.limit_train, args.seed)
    val_texts, val_y = load_split(args.val, args.limit_val, args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)
    t0 = time.time()
    train_enc, val_enc = encode(tokenizer, train_texts, args.max_chunks), encode(tokenizer, val_texts, args.max_chunks)
    chunks = [len(e[0]) for e in train_enc]
    print(f"Device {device}. Train {len(train_enc)} resumes ({sum(chunks)} chunks), val {len(val_enc)}. "
          f"Tokenised in {time.time() - t0:.0f}s.")

    baseline = {c: majority_baseline([y[j] for y in train_y], [y[j] for y in val_y]) for j, c in enumerate(CRITERIA)}
    print("Majority baseline (val macro-F1): " + ", ".join(f"{c.upper()} {b['macro_f1']}" for c, b in baseline.items()))

    model = ResumeRatingModel.from_checkpoint(args.checkpoint).to(device)
    weights = class_weights(train_y)
    losses = [nn.CrossEntropyLoss(weight=w.to(device)) for w in weights]
    print("Class weights: " + "; ".join(f"{c.upper()} {[round(x, 2) for x in w.tolist()]}" for c, w in zip(CRITERIA, weights)))

    optimiser = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = math.ceil(math.ceil(len(train_enc) / args.batch_size) / args.grad_accum) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimiser, int(steps * args.warmup), steps)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    rng = random.Random(args.seed)

    best, best_epoch, stale, history = -1.0, 0, 0, []
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, total, n_batches = time.time(), 0.0, 0
        optimiser.zero_grad()
        for step, (ids, mask, chunk_mask, y) in enumerate(batches(train_enc, train_y, args.batch_size, True, rng), 1):
            ids, mask, chunk_mask, y = ids.to(device), mask.to(device), chunk_mask.to(device), y.to(device)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(ids, mask, chunk_mask)
            loss = sum(losses[j](logits[:, j].float(), y[:, j]) for j in range(len(CRITERIA)))
            scaler.scale(loss / args.grad_accum).backward()
            if step % args.grad_accum == 0:
                scaler.unscale_(optimiser)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimiser)
                scaler.update()
                scheduler.step()
                optimiser.zero_grad()
            total += loss.item()
            n_batches += 1
        if n_batches % args.grad_accum:  # apply the last partial accumulation
            scaler.unscale_(optimiser)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimiser)
            scaler.update()
            scheduler.step()
            optimiser.zero_grad()

        per, mean_f1 = evaluate(model, val_enc, val_y, device, args.batch_size)
        history.append({"epoch": epoch, "train_loss": round(total / max(n_batches, 1), 4),
                        "val_mean_macro_f1": round(mean_f1, 4), "val": per, "seconds": round(time.time() - t0)})
        print(f"epoch {epoch}: train_loss={total / max(n_batches, 1):.4f} val_mean_macro_f1={mean_f1:.4f} "
              + " ".join(f"val_{c}_f1={per[c]['macro_f1']} val_{c}_qwk={per[c]['qwk']}" for c in CRITERIA)
              + f" ({time.time() - t0:.0f}s)")

        if mean_f1 > best:
            best, best_epoch, stale = mean_f1, epoch, 0
            save_model(model, tokenizer, args.model_dir, extra={
                "checkpoint": args.checkpoint, "best_epoch": epoch, "val_mean_macro_f1": round(mean_f1, 4),
                "val_metrics": per, "majority_baseline_val": baseline, "max_chunks": args.max_chunks,
                "hyperparameters": {k: v for k, v in vars(args).items() if k not in ("train", "val", "model_dir")}})
        else:
            stale += 1
            if stale >= args.patience:
                print(f"No better validation macro-F1 for {stale} epochs; stopping.")
                break

    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    (Path(args.model_dir) / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"Best epoch {best_epoch}: val mean macro-F1 {best:.4f}. Model saved to {args.model_dir}")


if __name__ == "__main__":
    main()