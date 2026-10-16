"""Link each curated skill to an ESCO concept and an O*NET software example where an exact match exists.

Fills the esco_uri and onet_example columns of the vocabulary file in place.

Usage:
    python knowledge-base-pipeline/link_skill_vocabulary.py knowledge-base-pipeline/skill_vocabulary.csv
        data/raw/esco/skills_en.csv data/raw/esco/digitalSkillsCollection_en.csv data/raw/onet/software_skills.csv
"""

import argparse
import re

import pandas as pd

ONET_OCCUPATIONS = r"15-12|15-2051"  # computer occupations and data scientists
VENDOR_PREFIX = re.compile(
    r"^(?:microsoft|oracle|ibm|amazon|google|apache|atlassian|adobe|red hat|vmware|jetbrains|the mathworks)\s+",
    re.IGNORECASE,
)
# Equivalents checked by hand where the ESCO preferred label differs from the skill name
ESCO_EQUIVALENTS = {
    "Microsoft SQL Server": "SQL Server",
    "Apache Spark": "SPARK",
    "Maven": "Apache Maven",
    "Teradata": "Teradata Database",
    "SSIS": "SQL Server Integration Services",
    "Data warehousing": "data warehouse",
    "Database design": "data models",
    "Data analysis": "data analytics",
    "ETL": "data extraction, transformation and loading tools",
    "Cybersecurity": "cyber security",
    "Cloud computing": "cloud technologies",
    "Cloud security": "cloud security and compliance",
    "Application security": "web application security threats",
    "Identity and access management": "digital identity management",
    "Encryption": "ICT encryption",
    "DevOps practices": "DevOps",
    "IoT": "Internet of Things",
    "Test automation": "tools for ICT test automation",
    "UML": "unified modelling language",
    "BPMN": "business process modelling",
    "Interaction design": "software interaction design",
    "Agile": "Agile development",
    "SEO": "search engine optimisation",
    "DNS": "domain name service",
    "Active Directory": "distributed directory information services",
    "Microsoft Excel": "use spreadsheets software",
}
# Corrections where an exact match picked the wrong O*NET example ("" removes the link)
ONET_FIXES = {"iOS": "Apple iOS", "Teradata": "Teradata Database", "Data pipelines": ""}


def normalise(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def split_aliases(value):
    return [alias.strip() for alias in str(value).split(";") if alias.strip()] if isinstance(value, str) else []


def esco_concepts(skills_csv, digital_csv):
    """Preferred label (with and without its bracketed note) to concept URI, digital skills first."""
    concepts = pd.read_csv(skills_csv)
    concepts = concepts[concepts["status"] == "released"]
    digital = set(pd.read_csv(digital_csv)["conceptUri"])
    by_label = {}
    for uri, label in concepts[["conceptUri", "preferredLabel"]].itertuples(index=False):
        for key in {normalise(label), normalise(re.sub(r"\s*\(.*?\)\s*$", "", label))}:
            by_label.setdefault(key, []).append((uri not in digital, uri))
    return {key: sorted(matches)[0][1] for key, matches in by_label.items()}, dict(
        zip(concepts["preferredLabel"], concepts["conceptUri"])
    )


def onet_examples(software_skills_csv):
    """Each form of an example ("Microsoft Power BI", "power bi", ...) to the example itself."""
    examples = pd.read_csv(software_skills_csv)
    computing = examples[examples["O*NET-SOC Code"].str.match(ONET_OCCUPATIONS)]["Workplace Example"].unique()
    forms = {}
    for example in computing:
        base = re.sub(r"\s+software$", "", example, flags=re.IGNORECASE)
        keys = {normalise(example), normalise(base), normalise(VENDOR_PREFIX.sub("", base))}
        acronym = re.match(r"^(.*?)\s+([A-Z][A-Za-z0-9.+#/-]*[A-Z0-9])$", base)
        if acronym:
            keys |= {normalise(part) for part in acronym.groups()}
        for key in keys:
            forms.setdefault(key, example)
    return forms, set(examples["Workplace Example"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vocabulary_csv")
    parser.add_argument("esco_skills_csv")
    parser.add_argument("esco_digital_skills_csv")
    parser.add_argument("onet_software_skills_csv")
    args = parser.parse_args()

    vocabulary = pd.read_csv(args.vocabulary_csv)
    esco_by_name, esco_by_label = esco_concepts(args.esco_skills_csv, args.esco_digital_skills_csv)
    onet_by_form, all_onet_examples = onet_examples(args.onet_software_skills_csv)

    esco_uris, onet_links = [], []
    for skill, aliases, case_sensitive in vocabulary[["skill", "aliases", "case_sensitive_aliases"]].itertuples(
        index=False
    ):
        if skill in ESCO_EQUIVALENTS:
            esco_uris.append(esco_by_label[ESCO_EQUIVALENTS[skill]])
        else:
            esco_uris.append(esco_by_name.get(normalise(skill), ""))

        if skill in ONET_FIXES:
            fixed = ONET_FIXES[skill]
            if fixed and fixed not in all_onet_examples:
                raise SystemExit(f"Unknown O*NET example in ONET_FIXES: {fixed}")
            onet_links.append(fixed)
        else:
            keys = [normalise(skill)] + [
                normalise(alias) for alias in split_aliases(aliases) + split_aliases(case_sensitive)
            ]
            onet_links.append(next((onet_by_form[key] for key in keys if key in onet_by_form), ""))

    vocabulary = vocabulary.assign(esco_uri=esco_uris, onet_example=onet_links)
    vocabulary.to_csv(args.vocabulary_csv, index=False)

    esco, onet = vocabulary["esco_uri"] != "", vocabulary["onet_example"] != ""
    print(
        f"{len(vocabulary)} skills: {esco.sum()} linked to ESCO, {onet.sum()} to O*NET, "
        f"{(esco | onet).sum()} to at least one, {(~esco & ~onet).sum()} to neither"
    )


if __name__ == "__main__":
    main()