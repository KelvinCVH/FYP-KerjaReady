"""Build the skill embedding folder used for semantic skill matching (KR-94).

Downloads the int8 ONNX export of granite-embedding-small-english-r2 from Hugging Face, embeds every skill name
in the vocabulary with the same code the assess-resume Lambda uses, and runs a small sanity check.

Usage (from the repo root):
    python knowledge-base-pipeline/build_skill_embeddings.py knowledge-base-pipeline/skill_vocabulary.csv
        data/skill-embedding/kerjaready-skill-embedding-YYYYMMDD
The folder name becomes the version. Rebuild with --revision <commit> to get the same model files again.
"""

import argparse
import csv
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from huggingface_hub import HfApi, hf_hub_download

# Same embedding code as the Lambda, so skill vectors and resume line vectors always match
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "functions" / "assess-resume"))
from skill_embedding_model import SkillEmbeddingModel  # noqa: E402

MODEL_ID = "onnx-community/granite-embedding-small-english-r2-ONNX"
MODEL_FILE = "model_quantized.onnx"  # int8; the weights are in model_quantized.onnx_data next to it
FILES = [f"onnx/{MODEL_FILE}", f"onnx/{MODEL_FILE}_data", "tokenizer.json"]

# (skill, a line that evidences it, a line that does not): the first line should score higher
SANITY_PAIRS = [
    ("Machine learning", "Trained a gradient boosting model to predict customer churn",
     "Configured VLANs and OSPF routing on Cisco switches"),
    ("Agile", "Worked in two-week sprints with daily stand-ups and sprint reviews",
     "Wrote unit tests for the payment service in JUnit"),
    ("Data visualisation", "Built Power BI dashboards showing monthly sales by region",
     "Set up a CI/CD pipeline with GitHub Actions"),
    ("Java", "Developed REST APIs with Spring Boot",
     "Built interactive pages with React and JavaScript"),
]


def read_skill_names(vocabulary_csv):
    with open(vocabulary_csv, newline="", encoding="utf-8") as file:
        names = [row["skill"].strip() for row in csv.DictReader(file)]
    if len(names) != len(set(names)):
        raise ValueError("Skill names in the vocabulary must be unique")
    return names


def download_model(out, revision):
    """Copy the model files into out; return the full commit they came from."""
    commit = HfApi().model_info(MODEL_ID, revision=revision).sha
    for name in FILES:
        shutil.copy(hf_hub_download(MODEL_ID, name, revision=commit), out / Path(name).name)
    model_config = json.loads(Path(hf_hub_download(MODEL_ID, "config.json", revision=commit)).read_text(encoding="utf-8"))
    return commit, model_config


def sanity_check(model):
    print("\nSanity check: the evidence line should score higher than the other line")
    for skill, evidence, other in SANITY_PAIRS:
        skill_vector, evidence_vector, other_vector = model.embed([skill, evidence, other])
        good, bad = float(skill_vector @ evidence_vector), float(skill_vector @ other_vector)
        print(f"  {skill:<20} evidence {good:.3f}  other {bad:.3f}  {'ok' if good > bad else 'CHECK'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vocabulary_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--revision", default="main", help="Hugging Face branch or commit of the model repo")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    commit, model_config = download_model(out, args.revision)
    config = {
        "version": out.name,
        "model_id": MODEL_ID,
        "revision": commit,
        "model_file": MODEL_FILE,
        "pad_token_id": model_config["pad_token_id"],
        "dimension": model_config["hidden_size"],
        "skill_text": "skill name",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "embedding_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    names = read_skill_names(args.vocabulary_csv)
    started = time.time()
    model = SkillEmbeddingModel(out)
    loaded = time.time()
    vectors = model.embed(names)
    np.save(out / "skill_vectors.npy", vectors)
    (out / "skill_names.json").write_text(json.dumps(names, indent=1), encoding="utf-8")
    print(f"Model {MODEL_ID} at {commit[:7]}: loaded in {loaded - started:.1f} s, "
          f"{len(names)} skills embedded in {time.time() - loaded:.1f} s -> {out}")

    sanity_check(model)


if __name__ == "__main__":
    main()