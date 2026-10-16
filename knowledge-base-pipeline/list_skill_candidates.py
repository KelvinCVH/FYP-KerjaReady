"""List skill candidates from O*NET and ESCO, with how many cleaned postings mention each one.

The output is the evidence used to curate knowledge-base-pipeline/skill_vocabulary.csv by hand.

Usage:
    python knowledge-base-pipeline/list_skill_candidates.py data/clean/clean-job-postings.csv
        data/raw/onet/software_skills.csv data/raw/esco/digitalSkillsCollection_en.csv
        data/clean/skill-candidates.csv
"""

import argparse
import re
from collections import defaultdict

import ahocorasick
import pandas as pd

ONET_OCCUPATIONS = r"15-12|15-2051"  # computer occupations and data scientists
VENDOR_PREFIX = re.compile(
    r"^(?:microsoft|oracle|ibm|amazon|google|apache|atlassian|adobe|sap|red hat|vmware|cisco|jetbrains|the)\s+",
    re.IGNORECASE,
)
MAX_ALIAS_LENGTH = 40


def onet_aliases(example):
    """ "Structured query language SQL" gives "structured query language" and "sql"."""
    base = re.sub(r"\s+software$", "", example, flags=re.IGNORECASE)
    aliases = {example, base}
    acronym = re.match(r"^(.*?)\s+([A-Z][A-Z0-9.+#/-]{1,})$", base)
    if acronym:
        aliases.update(acronym.groups())
    without_vendor = VENDOR_PREFIX.sub("", base)
    if without_vendor != base and len(without_vendor) > 3:
        aliases.add(without_vendor)
    return {alias.strip().lower() for alias in aliases if len(alias.strip()) > 1}


def esco_aliases(preferred_label, alt_labels):
    """ "Python (computer programming)" gives "python", plus the alternative labels."""
    aliases = {re.sub(r"\s*\(.*?\)\s*$", "", preferred_label)}
    if isinstance(alt_labels, str):
        aliases.update(label.strip() for label in alt_labels.split("|") if len(label.strip()) < MAX_ALIAS_LENGTH)
    return {alias.lower() for alias in aliases if alias}


def load_candidates(onet_csv, esco_digital_csv):
    onet = pd.read_csv(onet_csv)
    onet = onet[onet["O*NET-SOC Code"].str.match(ONET_OCCUPATIONS)]
    candidates = {example: ("O*NET", onet_aliases(example)) for example in onet["Workplace Example"].unique()}

    esco = pd.read_csv(esco_digital_csv)
    esco = esco[esco["skillType"] == "knowledge"]
    for label, alt_labels in esco[["preferredLabel", "altLabels"]].itertuples(index=False):
        source, aliases = candidates.setdefault(label, ("ESCO", set()))
        aliases.update(esco_aliases(label, alt_labels))
    return candidates


def is_whole_word(text, start, end):
    before = text[start - 1] if start > 0 else " "
    after = text[end + 1] if end + 1 < len(text) else " "
    return not (before.isalnum() or before in "+#_") and not (after.isalnum() or after in "+#_")


def postings_per_alias(descriptions, aliases):
    automaton = ahocorasick.Automaton()
    for alias in aliases:
        automaton.add_word(alias, alias)
    automaton.make_automaton()

    postings = defaultdict(set)
    for number, description in enumerate(descriptions):
        text = description.lower()
        for end, alias in automaton.iter(text):
            if is_whole_word(text, end - len(alias) + 1, end):
                postings[alias].add(number)
    return postings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cleaned_csv")
    parser.add_argument("onet_software_skills_csv")
    parser.add_argument("esco_digital_skills_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()

    descriptions = pd.read_csv(args.cleaned_csv)["description"].tolist()
    candidates = load_candidates(args.onet_software_skills_csv, args.esco_digital_skills_csv)
    postings = postings_per_alias(descriptions, {alias for _, aliases in candidates.values() for alias in aliases})

    rows = []
    for candidate, (source, aliases) in candidates.items():
        matched = set().union(*(postings.get(alias, set()) for alias in aliases))
        hits = sorted(((alias, len(postings.get(alias, ()))) for alias in aliases), key=lambda hit: -hit[1])
        alias_hits = "; ".join(f"{alias}: {count}" for alias, count in hits if count)
        rows.append({"candidate": candidate, "source": source, "postings": len(matched), "alias_hits": alias_hits})

    table = pd.DataFrame(rows).sort_values("postings", ascending=False)
    table.to_csv(args.output_csv, index=False)
    print(f"{len(table):,} candidates, {(table['postings'] >= 5).sum():,} mentioned by 5 or more postings")


if __name__ == "__main__":
    main()