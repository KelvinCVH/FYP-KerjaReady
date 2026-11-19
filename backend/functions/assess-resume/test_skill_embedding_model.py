"""Tests for the skill embedding model. Run: python -m pytest backend/functions/assess-resume

The real-model test runs only when the built folder is at skill_embedding/ (or SKILL_EMBEDDING_DIR).
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import skill_embedding_model
from skill_embedding_model import BATCH_SIZE, SkillEmbeddingModel

REAL_MODEL_DIR = Path(os.environ.get("SKILL_EMBEDDING_DIR", Path(__file__).resolve().parent / "skill_embedding"))


class FakeTokenizer:
    """One token per word: the id is the word length. Pads to the longest text in the batch."""

    def enable_truncation(self, max_length):
        pass

    def enable_padding(self, pad_id, pad_token):
        self.pad_id = pad_id

    def id_to_token(self, token_id):
        return "[PAD]"

    def encode_batch(self, texts):
        rows = [[1] + [len(word) for word in text.split()] for text in texts]
        width = max(len(row) for row in rows)
        return [SimpleNamespace(ids=row + [self.pad_id] * (width - len(row)),
                                attention_mask=[1] * len(row) + [0] * (width - len(row))) for row in rows]


class FakeSession:
    """Embeds a text as (number of words, total word length, 1); pooled or as token vectors."""

    def __init__(self, path, providers, pooled=True):
        self.pooled = pooled

    def get_inputs(self):
        return [SimpleNamespace(name="input_ids"), SimpleNamespace(name="attention_mask")]

    def get_outputs(self):
        return [SimpleNamespace(name="sentence_embedding" if self.pooled else "last_hidden_state")]

    def run(self, names, feed):
        assert set(feed) == {"input_ids", "attention_mask"}
        mask = feed["attention_mask"]
        words = mask.sum(axis=1) - 1
        lengths = (feed["input_ids"] * mask).sum(axis=1) - 1
        pooled = np.stack([words, lengths, np.ones_like(words)], axis=1).astype(np.float32)
        if self.pooled:
            return [pooled]
        tokens = np.zeros((len(pooled), mask.shape[1], 3), dtype=np.float32)
        tokens[:, 0] = pooled  # [CLS] position
        return [tokens]


def make_folder(tmp_path, names=None, vectors=None):
    config = {"version": "test", "model_file": "model.onnx", "pad_token_id": 0, "dimension": 3}
    (tmp_path / "embedding_config.json").write_text(json.dumps(config))
    if vectors is not None:
        (tmp_path / "skill_names.json").write_text(json.dumps(names))
        np.save(tmp_path / "skill_vectors.npy", np.asarray(vectors, dtype=np.float32))
    return tmp_path


@pytest.fixture
def fakes(monkeypatch):
    def use(pooled=True):
        monkeypatch.setattr(skill_embedding_model.Tokenizer, "from_file", lambda path: FakeTokenizer())
        monkeypatch.setattr(skill_embedding_model.ort, "InferenceSession",
                            lambda path, providers: FakeSession(path, providers, pooled))
    return use


def expected_vector(text):
    words = text.split()
    vector = np.array([len(words), sum(len(w) for w in words), 1.0])
    return vector / np.linalg.norm(vector)


def test_embed_returns_unit_vectors_in_order_across_batches(tmp_path, fakes):
    fakes()
    model = SkillEmbeddingModel(make_folder(tmp_path))
    texts = [" ".join(["word"] * (i % 7 + 1)) + "s" * i for i in range(BATCH_SIZE * 2 + 5)]
    vectors = model.embed(texts)
    assert vectors.shape == (len(texts), 3)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)
    assert np.allclose(vectors, [expected_vector(t) for t in texts], atol=1e-6)


def test_uses_the_cls_token_when_the_model_gives_token_vectors(tmp_path, fakes):
    fakes(pooled=False)
    model = SkillEmbeddingModel(make_folder(tmp_path))
    assert np.allclose(model.embed(["Built Power BI dashboards"])[0], expected_vector("Built Power BI dashboards"))


def test_empty_list_gives_no_vectors(tmp_path, fakes):
    fakes()
    assert SkillEmbeddingModel(make_folder(tmp_path)).embed([]).shape == (0, 3)


def test_loads_skill_vectors_and_rejects_a_mismatch(tmp_path, fakes):
    fakes()
    model = SkillEmbeddingModel(make_folder(tmp_path, ["Python", "SQL"], np.eye(3)[:2]))
    assert model.skill_names == ["Python", "SQL"] and model.skill_vectors.shape == (2, 3)
    make_folder(tmp_path, ["Python", "SQL"], np.eye(3))  # three vectors for two names
    with pytest.raises(ValueError):
        SkillEmbeddingModel(tmp_path)


@pytest.mark.skipif(not (REAL_MODEL_DIR / "embedding_config.json").exists(), reason="built skill_embedding folder not present")
def test_real_model_scores_evidence_above_an_unrelated_line():
    model = SkillEmbeddingModel(REAL_MODEL_DIR)
    skill, evidence, other = model.embed([
        "Machine learning",
        "Trained a gradient boosting model to predict customer churn",
        "Configured VLANs and OSPF routing on Cisco switches",
    ])
    assert skill @ evidence > skill @ other
    assert len(model.skill_names) == len(model.skill_vectors)