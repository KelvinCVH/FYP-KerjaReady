"""Sentence embeddings for semantic skill matching (KR-94).

Model: granite-embedding-small-english-r2 (IBM, Apache 2.0), the int8 ONNX export from onnx-community,
run on CPU with ONNX Runtime. Texts are short (a skill name or one resume line), so each is cut at MAX_TOKENS.

The folder is built by knowledge-base-pipeline/build_skill_embeddings.py and holds:
  embedding_config.json                 version, model id and revision, model file, pad token id, dimension
  tokenizer.json, model_quantized.onnx and model_quantized.onnx_data
  skill_names.json, skill_vectors.npy   one unit vector per vocabulary skill, same order (absent while building)
"""

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MAX_TOKENS = 128
BATCH_SIZE = 32


def unit_vectors(vectors):
    """Scale each row to length 1, so a dot product is the cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return (vectors / np.maximum(norms, 1e-12)).astype(np.float32)


class SkillEmbeddingModel:
    def __init__(self, model_dir):
        d = Path(model_dir)
        self.config = json.loads((d / "embedding_config.json").read_text(encoding="utf-8"))
        self.version = self.config["version"]
        self.dimension = self.config["dimension"]

        pad_id = self.config["pad_token_id"]
        self.tokenizer = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        self.tokenizer.enable_padding(pad_id=pad_id, pad_token=self.tokenizer.id_to_token(pad_id))

        self.session = ort.InferenceSession(str(d / self.config["model_file"]), providers=["CPUExecutionProvider"])
        self.input_names = {item.name for item in self.session.get_inputs()}
        self.output_names = [item.name for item in self.session.get_outputs()]

        # Skill vectors exist in the deployed folder; the build script loads the model before it makes them
        self.skill_names, self.skill_vectors = None, None
        if (d / "skill_vectors.npy").exists():
            names = json.loads((d / "skill_names.json").read_text(encoding="utf-8"))
            vectors = np.load(d / "skill_vectors.npy")
            if vectors.shape != (len(names), self.dimension):
                raise ValueError(f"skill_vectors.npy is {vectors.shape}, expected ({len(names)}, {self.dimension})")
            self.skill_names, self.skill_vectors = names, vectors

    def embed(self, texts):
        """One unit vector per text, in the same order: shape (len(texts), dimension)."""
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        batches = []
        for start in range(0, len(texts), BATCH_SIZE):
            encodings = self.tokenizer.encode_batch(list(texts[start:start + BATCH_SIZE]))
            ids = np.array([e.ids for e in encodings], dtype=np.int64)
            feed = {
                "input_ids": ids,
                "attention_mask": np.array([e.attention_mask for e in encodings], dtype=np.int64),
                "token_type_ids": np.zeros_like(ids),  # only BERT-style models such as bge-small ask for this
            }
            outputs = dict(zip(self.output_names, self.session.run(None, {k: v for k, v in feed.items() if k in self.input_names})))
            # The onnx-community export pools into sentence_embedding; a plain export gives token vectors, [CLS] first
            pooled = outputs["sentence_embedding"] if "sentence_embedding" in outputs else outputs["last_hidden_state"][:, 0]
            batches.append(pooled)
        return unit_vectors(np.concatenate(batches))