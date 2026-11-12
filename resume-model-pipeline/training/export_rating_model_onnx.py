import argparse
import json
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from transformers.utils import logging as hf_logging

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "backend" / "functions" / "assess-resume"))  # the Lambda function code
from rating_model import CRITERIA, chunk_resume, load_model
from onnx_rating_model import OnnxRatingModel

def export(model, tokenizer, example_text, max_chunks, path):
    ids, att = chunk_resume(tokenizer, example_text, max_chunks)
    inputs = (torch.tensor([ids]), torch.tensor([att]), torch.ones(1, len(ids), dtype=torch.long))
    chunks = torch.export.Dim("chunks", min=1, max=max_chunks)
    torch.onnx.export(model, inputs, str(path), dynamo=True, external_data=False,
                      input_names=["input_ids", "attention_mask", "chunk_mask"], output_names=["logits"],
                      dynamic_shapes={"input_ids": {1: chunks}, "attention_mask":{1: chunks}, "chunk_mask": {1: chunks}})

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model-dir", required=True, help="Unpacked model folder from the training job")
    p.add_argument("--test", default="data/splits_2000/test.csv")
    args = p.parse_args(argv)
    hf_logging.set_verbosity_error()
 
    model_dir = Path(args.model_dir)
    out = model_dir / "onnx"
    out.mkdir(parents=True, exist_ok=True)
    model, tokenizer = load_model(model_dir)
    config = json.loads((model_dir / "rating_config.json").read_text(encoding="utf-8"))
    texts = pd.read_csv(args.test, dtype=str, keep_default_na=False)["text"].tolist()
 
    # export with a resume that has at least two chunks, so the chunk axis is clearly variable
    example = next((t for t in texts if len(chunk_resume(tokenizer, t, config["max_chunks"])[0]) >= 2), texts[0])
    print("Exporting to ONNX...")
    export(model, tokenizer, example, config["max_chunks"], out / "rating_model.onnx")
    shutil.copy(model_dir / "tokenizer" / "tokenizer.json", out / "tokenizer.json")
    runtime_config = {"criteria": CRITERIA, "chunk_tokens": config["chunk_tokens"], "max_chunks": config["max_chunks"],
                      "cls_token_id": tokenizer.cls_token_id, "sep_token_id": tokenizer.sep_token_id,
                      "pad_token_id": tokenizer.pad_token_id, "unk_token_id": tokenizer.unk_token_id,
                      "source_model": model_dir.name, "best_epoch": config.get("best_epoch")}
    (out / "rating_config.json").write_text(json.dumps(runtime_config, indent=2), encoding="utf-8")
 
    print(f"Checking {len(texts)} test resumes: ONNX against PyTorch")
    onnx_model = OnnxRatingModel(out)
    token_mismatch, level_mismatch, worst = 0, 0, 0.0
    for text in texts:
        ids, att = chunk_resume(tokenizer, text, config["max_chunks"])
        onnx_ids, _, _ = onnx_model.encode(text)
        token_mismatch += int(not np.array_equal(np.array([ids]), onnx_ids))
        with torch.no_grad():
            ref = model(torch.tensor([ids]), torch.tensor([att]), torch.ones(1, len(ids), dtype=torch.long))[0].numpy()
        got = onnx_model.logits(text)
        worst = max(worst, float(np.abs(got - ref).max()))
        level_mismatch += int((got.argmax(-1) != ref.argmax(-1)).any())
    size_mb = (out / "rating_model.onnx").stat().st_size / 1e6
    print(f"Token mismatches: {token_mismatch}. Resumes with a different level: {level_mismatch}. "
          f"Largest score difference: {worst:.2e}. ONNX file: {size_mb:.0f} MB")
    if token_mismatch or level_mismatch:
        sys.exit("ONNX does not match PyTorch; do not deploy this export.")
    print(f"OK. Deploy the three files in {out}")
 
 
if __name__ == "__main__":
    main()
                                                    