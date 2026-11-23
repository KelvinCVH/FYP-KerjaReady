"""Draw resume line and skill pairs to label by hand, for calibrating the semantic skill match (KR-94).

Resumes come from the resume model's test split. The corpus has no line breaks, so each resume is split into
lines with the labelling tool's splitter (resume_structure.to_lines). Then the same steps as the Lambda run:
the rule-based match first, and for every other skill the best line under each score ("raw" and "relative").

One unit is one resume and one skill. Units are drawn per band of the relative score, more from the high
bands where the threshold will sit. Each unit keeps a weight (units in its band / units drawn from it), so the
precision and recall worked out later describe all units, not only the drawn ones.

Usage (from the repo root):
    python knowledge-base-pipeline/draw_skill_match_pairs.py resume-model-pipeline/data/splits/test.csv
        data/skill-match-calibration

Outputs
    pairs_to_label.csv   pair_id, skill, line, evidenced. Fill evidenced with 1 or 0. No scores, so labels are blind.
    pairs_key.csv        one row per unit: resume, skill, best line and score under each score, band, weight
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend" / "functions" / "assess-resume"))
sys.path.insert(0, str(REPO / "resume-model-pipeline"))
from match_resume_skills import line_skill_scores, semantic_lines  # noqa: E402
from resume_structure import to_lines  # noqa: E402
from skill_embedding_model import SkillEmbeddingModel  # noqa: E402
from skill_matching import find_skills, load_vocabulary  # noqa: E402

SEED = 94
RESUMES = 20
# (upper quantile of the relative score, units to draw): most units score low, so the top bands are drawn heavily
BANDS = [(0.80, 30), (0.95, 50), (0.99, 60), (1.00, 60)]


def resume_units(resume_id, text, vocabulary, model):
    """Every skill the rule-based match did not find, with its best line under each score."""
    lines = semantic_lines("\n".join(to_lines(text)))
    if not lines:
        return []
    lexical = find_skills("\n".join(lines), vocabulary)
    scores = line_skill_scores(lines, model)
    units = []
    for column, skill in enumerate(model.skill_names):
        if skill in lexical:
            continue
        raw_best = int(np.argmax(scores["raw"][:, column]))
        relative_best = int(np.argmax(scores["relative"][:, column]))
        units.append({
            "resume_id": resume_id,
            "skill": skill,
            "raw_line": lines[raw_best],
            "raw_score": round(float(scores["raw"][raw_best, column]), 4),
            "relative_line": lines[relative_best],
            "relative_score": round(float(scores["relative"][relative_best, column]), 4),
        })
    return units


def draw_units(units, rng):
    """Units drawn per relative-score band, each with its weight."""
    units = units.sort_values("relative_score", kind="stable").reset_index(drop=True)
    drawn, start = [], 0
    for band, (upper, wanted) in enumerate(BANDS, start=1):
        end = len(units) if upper == 1.00 else int(round(len(units) * upper))
        members = list(range(start, end))
        chosen = rng.sample(members, min(wanted, len(members)))
        for index in chosen:
            drawn.append({**units.loc[index].to_dict(), "band": band, "weight": len(members) / len(chosen)})
        start = end
    return pd.DataFrame(drawn)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_csv", help="test split from resume-model-pipeline/build_splits.py")
    parser.add_argument("out_dir")
    parser.add_argument("--model-dir", default=str(REPO / "backend" / "functions" / "assess-resume" / "skill_embedding"))
    args = parser.parse_args()

    model = SkillEmbeddingModel(args.model_dir)
    vocabulary = load_vocabulary(Path(args.model_dir) / "skill_vocabulary.csv")
    rng = random.Random(SEED)

    resumes = pd.read_csv(args.test_csv, dtype=str, keep_default_na=False)
    resumes = resumes.loc[rng.sample(list(resumes.index), min(RESUMES, len(resumes)))]
    units = pd.DataFrame([u for _, r in resumes.iterrows() for u in resume_units(r["resume_id"], r["text"], vocabulary, model)])
    drawn = draw_units(units, rng)

    # One pair per distinct (skill, line); a unit whose two best lines differ needs both labelled
    pairs = pd.concat([drawn[["skill", "raw_line"]].set_axis(["skill", "line"], axis=1),
                       drawn[["skill", "relative_line"]].set_axis(["skill", "line"], axis=1)]).drop_duplicates()
    pairs = pairs.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffled, so bands are not visible
    pairs.insert(0, "pair_id", [f"P{n:03d}" for n in range(1, len(pairs) + 1)])
    pair_ids = {(row.skill, row.line): row.pair_id for row in pairs.itertuples()}
    drawn["raw_pair_id"] = [pair_ids[(s, line)] for s, line in zip(drawn["skill"], drawn["raw_line"])]
    drawn["relative_pair_id"] = [pair_ids[(s, line)] for s, line in zip(drawn["skill"], drawn["relative_line"])]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pairs.assign(evidenced="").to_csv(out / "pairs_to_label.csv", index=False, encoding="utf-8-sig")
    drawn.to_csv(out / "pairs_key.csv", index=False, encoding="utf-8")
    print(f"{len(resumes)} resumes, {len(units)} units (resume and skill), {len(drawn)} drawn, "
          f"{len(pairs)} pairs to label -> {out / 'pairs_to_label.csv'}")
    print(drawn.groupby("band").agg(units=("weight", "size"), weight=("weight", "first"),
                                    lowest_relative=("relative_score", "min")).to_string())


if __name__ == "__main__":
    main()