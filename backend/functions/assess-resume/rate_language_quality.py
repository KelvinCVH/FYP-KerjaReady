"""B2 Language Quality: count distinct errors with a self-hosted LanguageTool server and map the count to a level.

Rubric v1.0 / guide v1.4: 0 errors gives level 3, 1 or 2 errors give level 2, 3 or more give level 1.
Counted: spelling, grammar, confused words, capitalisation and misspelled product names ("Power Point").
Not counted, as in the guide:
  * British or American spelling: a spelling error counts only if both en-GB and en-US flag it
  * words with a capital letter (product, company and place names, "iBatis") and words written in capitals
  * words run together by text extraction ("usingautomated", "withiterationand"), spacing, punctuation style
  * style advice, including hyphen and compound-word conventions ("problem solving", "day to day")
Not checked: tense consistency and level 0 (both stated as limitations).

The server URL comes from LANGUAGETOOL_URL (default http://localhost:8081/v2/check).
Try it on a few resumes:  python inference/rate_language_quality.py data/splits_2000/val.csv --limit 5
"""

import argparse
import json
import os
import re
import urllib.parse
import urllib.request

LT_URL = os.environ.get("LANGUAGETOOL_URL", "http://localhost:8081/v2/check")
COUNTED_CATEGORIES = {"TYPOS", "GRAMMAR", "CONFUSED_WORDS", "CASING"}
# Hyphen and compound-word conventions are style, not errors; broken bullets start mid-sentence after extraction;
# lower-case file types ("pdf", "js") are a writing convention; "IT Support" is read as the pronoun "It";
# "in Windows" versus "on Windows" is a preference
IGNORED_RULES = re.compile(r"HYPHEN|COMPOUND|STAND_ALONE|FILE_EXTENSIONS_CASE|UPPERCASE_SENTENCE_START|IT_VBZ|IN_WINDOWS")
# A misspelling that starts or ends with one of these words is usually two words run together by extraction
JOINED_WORDS = ("with", "and", "the", "for", "using", "from", "into", "that", "this", "which", "were", "was")


def check(text, language, url=LT_URL, timeout=60):
    """Send text to LanguageTool and return its list of matches."""
    data = urllib.parse.urlencode({"text": text, "language": language}).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))["matches"]


def _span(text, m):
    return text[m["offset"]:m["offset"] + m["length"]]


def _is_spelling(m):
    """The dictionary spell checker; rule-based checks such as product names ("Power Point") are not filtered."""
    return m["rule"]["id"].startswith("MORFOLOGIK_RULE")


def _ignore_spelling(word, m):
    if not word or any(ch.isupper() or ch.isdigit() for ch in word):
        return True  # product, company or place names, versions; also covers words in capitals
    # run-together words from text extraction: LanguageTool suggests the same letters with a space,
    # or the word starts or ends with a common short word ("withiterationand")
    if any(r.get("value", "").replace(" ", "") == word for r in m.get("replacements", [])):
        return True
    lower = word.lower()
    return any((lower.startswith(w) or lower.endswith(w)) and len(lower) - len(w) >= 4 for w in JOINED_WORDS)


def count_errors(text, gb_matches, us_matches):
    """Distinct counted errors, from the en-GB matches and (for spelling) the en-US matches."""
    us_spelling = {(m["offset"], m["length"]) for m in us_matches if _is_spelling(m)}
    errors = {}
    for m in gb_matches:
        rule, category = m["rule"]["id"], m["rule"]["category"]["id"]
        if category not in COUNTED_CATEGORIES or IGNORED_RULES.search(rule) or "hyphen" in m.get("message", "").lower():
            continue
        word = _span(text, m)
        if _is_spelling(m) and (_ignore_spelling(word, m) or (m["offset"], m["length"]) not in us_spelling):
            continue
        key = (rule, word.lower())  # the same mistake repeated counts once
        errors.setdefault(key, {"text": word, "rule": rule, "message": m.get("message", "")})
    return list(errors.values())


def level_from_count(n):
    return 3 if n == 0 else 2 if n <= 2 else 1


def rate_b2(text, url=LT_URL):
    """Return (B2 level, list of counted errors)."""
    errors = count_errors(text, check(text, "en-GB", url), check(text, "en-US", url))
    return level_from_count(len(errors)), errors


def main(argv=None):
    import pandas as pd
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="CSV with resume_id and text")
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args(argv)
    d = pd.read_csv(args.csv, dtype=str, keep_default_na=False).head(args.limit)
    levels = []
    for rid, text in zip(d["resume_id"], d["text"]):
        level, errors = rate_b2(text)
        levels.append(level)
        print(f"\n{rid}: B2 level {level}, {len(errors)} distinct errors")
        for e in errors[:8]:
            print(f"  - {e['text']!r} ({e['rule']}): {e['message']}")
    print("\nLevels:", {lv: levels.count(lv) for lv in (1, 2, 3)})


if __name__ == "__main__":
    main()