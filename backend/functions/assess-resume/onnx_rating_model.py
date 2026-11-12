import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class OnnxRatingModel:
    def __init__(self, model_dir):
        d = Path(model_dir)
        cfg = json.loads((d / "rating_config.json").read_text(encoding="utf-8"))
        self.criteria = cfg["criteria"]
        self.version = cfg.get("source_model", "unknown")  # the training job the weights came from
        self.chunk_tokens, self.max_chunks = cfg["chunk_tokens"], cfg["max_chunks"]
        self.cls, self.sep, self.pad, self.unk = (cfg[k] for k in ("cls_token_id", "sep_token_id", "pad_token_id", "unk_token_id"))
        self.tokenizer = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.session = ort.InferenceSession(str(d / "rating_model.onnx"), providers=["CPUExecutionProvider"])

    def encode(self, text):
        """Return input_ids, attention_mask (1, chunks, 512) and chunk_mask (1, chunks) as int64 arrays."""
        ids = self.tokenizer.encode(text or "", add_special_tokens=False).ids or [self.unk]
        pieces = [ids[i:i + self.chunk_tokens] for i in range(0, len(ids), self.chunk_tokens)][:self.max_chunks]
        length = self.chunk_tokens + 2
        input_ids = np.full((1, len(pieces), length), self.pad, dtype=np.int64)
        attention = np.zeros((1, len(pieces), length), dtype=np.int64)
        for k, piece in enumerate(pieces):
            row = [self.cls] + piece + [self.sep]
            input_ids[0, k, :len(row)] = row
            attention[0, k, :len(row)] = 1
        return input_ids, attention, np.ones((1, len(pieces)), dtype=np.int64)

    def logits(self, text):
        input_ids, attention, chunk_mask = self.encode(text)
        return self.session.run(["logits"], {"input_ids": input_ids, "attention_mask": attention, "chunk_mask": chunk_mask})[0][0]

    def rate(self, text):
        """Return {"a1": level, "a2": level, "a3": level}, levels 0-3."""
        scores = self.logits(text)
        return {c: int(np.argmax(scores[j])) for j, c in enumerate(self.criteria)}