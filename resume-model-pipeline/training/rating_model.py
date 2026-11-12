import json
from pathlib import Path
import torch
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer

CHECKPOINT = "distilbert-base-uncased"
CRITERIA = ["a1", "a2", "a3"]
NUM_LEVELS = 4
CHUNK_TOKENS = 510
MAX_CHUNKS = 8

def chunk_resume(tokenizer, text, max_chunks=MAX_CHUNKS):
    """
    Split the resume into 512 token counts
    Return (input_ids, attention_mask) as lists of lists, one row per chunk
    """
    ids = tokenizer(text, add_special_tokens=False)["input_ids"] or [tokenizer.unk_token_id]
    pieces = [ids[i:i + CHUNK_TOKENS] for i in range(0, len(ids), CHUNK_TOKENS)][:max_chunks]
    length = CHUNK_TOKENS + 2
    input_ids, attention_mask = [],[]
    for piece in pieces:
        row = [tokenizer.cls_token_id] + piece + [tokenizer.sep_token_id]
        pad = length - len(row)
        input_ids.append(row + [tokenizer.pad_token_id] * pad)
        attention_mask.append([1] * len(row) + [0] * pad)
    return input_ids, attention_mask

class ResumeRatingModel(nn.Module):
    "Encode every chunk, average the chunk's [CLS] vectors, and applies one linear head per criterion"

    def __init__(self, encoder, dropout=0.1):
        super().__init__()
        self.encoder = encoder
        hidden = encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.heads = nn.ModuleList([nn.Linear(hidden, NUM_LEVELS) for _ in CRITERIA])

    def forward(self, input_ids, attention_mask, chunk_mask):
        """
        input_ids, attention_mask: (resumes, chunks, 512). chunk_mask: (resumes, chunks), 1 for a real chunk.
        Returns logits of shape (resumes, 3 criteria, 4 levels).
        """
        n, c, length = input_ids.shape
        hidden = self.encoder(input_ids=input_ids.reshape(n*c, length),
                              attention_mask = attention_mask.reshape(n*c, length)
                              ).last_hidden_state
        cls = hidden[:, 0].reshape(n, c, -1)
        weights = chunk_mask.unsqueeze(-1).to(cls.dtype)
        pooled = (cls*weights).sum(dim=1) / weights.sum(dim=1).clamp(min=1.0)
        pooled = self.dropout(pooled)
        return torch.stack([head(pooled) for head in self.heads], dim=1)

    @classmethod
    def from_checkpoint(cls, name_or_path):
        """New model with pretrained encoder weights for training"""
        return cls(AutoModel.from_pretrained(name_or_path))

def save_model(model, tokenizer, out_dir, extra=None):
    """
    Save the model and tokenizer for evaluation and ONNX export
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "rating_model.pt")
    model.encoder.config.save_pretrained(out / "encoder")
    tokenizer.save_pretrained(out / "tokenizer")
    config = {
        "criteria": CRITERIA,
        "num_levels": NUM_LEVELS,
        "chunk_tokens": CHUNK_TOKENS,
        "max_chunks": MAX_CHUNKS,
        **(extra or {})
    }
    (out / "rating_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

def load_model(model_dir, map_location="cpu"):
    """
    Load a saved model and tokenizer for evaluation and ONNX export
    """
    model_dir = Path(model_dir)
    encoder =AutoModel.from_config(AutoConfig.from_pretrained(model_dir / "encoder"))
    model=ResumeRatingModel(encoder)
    model.load_state_dict(torch.load(model_dir / "rating_model.pt", map_location=map_location))
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_dir / "tokenizer")
    return model, tokenizer

