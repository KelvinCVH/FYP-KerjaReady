"""Clean the raw JobStreet postings into entry-level postings, each mapped to one target role.

Usage:
    python knowledge-base-pipeline/clean_job_postings.py data/raw/job-dataset.csv data/clean/clean-job-postings.csv
"""

import argparse
import re

import pandas as pd

ICT_CATEGORY = "Information & Communication Technology"
RELATED_SUBCATEGORIES = {
    "Web & Interaction Design",  # UI/UX roles are listed under Design & Architecture
    "Mathematics, Statistics & Information Sciences",  # data roles are listed under Science & Technology
}


def any_of(*patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)


# Titles with these words are not entry level
SENIOR_TITLE = any_of(
    r"\b(?:senior|snr|sr|lead|leader|principal|head|manager|director|architect|chief)\b",
    r"\b(?:vp|vice president|supervisor|expert|mid[- ]level)\b|\bstaff (?:\w+ )?engineer",
    r"\b(?:ii|iii|iv)\b",  # level II and above
)
# Descriptions that call the role senior or mid-level despite a plain title
SENIOR_DESCRIPTION = any_of(
    r"\bthis (?:senior|mid-level)\b[^.]{0,40}\brole\b",
    r"\b(?:mid|senior)[- ]level role\b",
    r"track record as an? senior\b",
)
# Internship postings list lighter requirements than graduate jobs
INTERNSHIP_TITLE = any_of(r"\b(?:intern|interns|internship|industrial training|practical training)\b")
# Support, sales and training roles are not target roles, even when the title names a technology
EXCLUDED_TITLE = any_of(
    r"\b(?:support|help ?desk|service desk|technician)\b",
    r"\b(?:sales|presales|pre-sales|business development|account (?:manager|executive)|recruit\w*)\b",
    r"\b(?:trainer|training|lecturer|tutor|certification)\b",
    r"\bdatabase (?:administrator|admin|engineer)\b|\bdba\b",  # database administration is not a target role
    r"\bcnc\b|\bplc\b|\bmilling\b",  # machine programming, not software
)

# First match wins: specialised roles first, then named developer roles, then technology-based roles.
# Titles that mix two roles, such as System Analyst or Web Designer, match no rule and are left out.
ROLE_RULES = [
    (
        "Cybersecurity",
        any_of(
            r"cyber",
            r"\bsecurity (?:analyst|engineer|executive|operations|consultant|specialist|administrator)",
            r"information security|\bit security|infosec",
            r"\bsoc\b|penetration|\bpentest",
        ),
    ),
    (
        "QA / Software Tester",
        any_of(
            r"\bqa\b|\bqc\b|quality assurance",
            r"\btester\b|\bsdet\b|software test|automation test",
            r"\btest(?:ing)? (?:engineer|analyst|executive|specialist|automation)",
        ),
    ),
    (
        "AI/ML Engineer",
        any_of(
            # "AI Engineer", "AI Software Engineer", but not "AI-Assisted Development" or "AI Product Developer"
            r"\b(?:ai|a\.i\.|artificial intelligence)\b"
            r"(?![\s-]*(?:assisted|driven|native|powered|tools?|product|web)\b)"
            r"(?:[\s/&-]+\w+){0,2}?[\s/&-]+(?:engineer|developer|scientist|specialist|researcher)",
            r"(?:engineer|developer|scientist)\s*\((?:ai|ai/ml|artificial intelligence)\)",  # "Software Engineer (AI)"
            r"machine learning|\bml\b|mlops|deep learning|computer vision|\bnlp\b",
            r"\bllm\b|\bgen ?ai\b|generative ai|prompt engineer|agentic",
        ),
    ),
    ("Data Scientist", any_of(r"data scien")),
    ("Data Engineer", any_of(r"data engineer|big data|\betl\b|data warehouse|data platform|data integration")),
    (
        "Data Analyst",
        any_of(
            r"data analy|reporting analyst|analytics (?:executive|analyst|engineer)",
            r"\bbi\b|business intelligence|power ?bi|tableau|qlik|looker",
        ),
    ),
    (
        "Business Analyst",
        any_of(r"business analy|business systems? analyst|functional analyst"),
    ),
    (
        "UI/UX Designer",
        any_of(
            r"\bui\s*/?\s*ux\b|\bux\b|user experience",
            r"\bui designer|user interface designer|product designer|interaction designer",
        ),
    ),
    (
        "DevOps Engineer",
        any_of(r"devops|devsecops|site reliability|\bsre\b|platform engineer|release engineer|build engineer"),
    ),
    ("Mobile Developer", any_of(r"mobile|android|\bios\b|flutter|react native|kotlin|swift|\bapp developer")),
    ("Full Stack Developer", any_of(r"full[\s-]?stack|\bmern\b|\bmean stack")),
    ("Frontend Developer", any_of(r"front[\s-]?end|\bui developer|\breact(?:js|\.js)?\b|angular|\bvue")),
    ("Backend Developer", any_of(r"back[\s-]?end|\bapi developer|node(?:\.?js)?\b|golang|\bgo developer")),
    ("Cloud Engineer", any_of(r"\bcloud\b|\baws\b|\bazure\b|\bgcp\b")),
    (
        "Network / Systems Engineer",
        any_of(
            r"network|infrastructure|\bserver\b|\bnoc\b|data ?cent(?:er|re)",
            r"systems? (?:engineer|administrator|admin|executive)|sysadmin",
            r"\blinux\b|\bunix\b|wintel",
        ),
    ),
    (
        "Software Engineer",
        any_of(
            r"software|developer|programmer|programming|\bcoder\b",
            r"applications? (?:engineer|developer)",
        ),
    ),
]

FRESH_GRADUATE = any_of(r"fresh grad", r"no (?:prior |working )?experience (?:is )?(?:required|needed)")
NUMBER_WORDS = dict(zip("one two three four five six seven eight nine ten".split(), range(1, 11)))
NUMBER = rf"(\d+|{'|'.join(NUMBER_WORDS)})"
RANGE_END = r"(?:\s*(?:-|–|to)\s*\d+)?"
YEARS = r"\s*years?(?:\(s\))?['’]?"
# Each pattern captures the minimum number of years a posting asks for
YEARS_OF_EXPERIENCE = [
    # "2-3 years of working experience", "3 or more years of experience", "5 years’ experience"
    re.compile(
        rf"{NUMBER}\s*(?:\(\d+\)\s*)?(?:\++|plus|or more|or above|and above)?{RANGE_END}\s*"
        rf"(?:\++)?{YEARS}\s*(?:of\s+)?(?:[\w/&,.()-]+\s+){{0,6}}?experience",
        re.IGNORECASE,
    ),
    # "Experience: 3 years", "Proven experience (10 years)"
    re.compile(rf"experience\s*[:(]\s*(?:at least\s+|minimum\s+)?{NUMBER}\s*\+*{RANGE_END}{YEARS}", re.IGNORECASE),
    # "3+ years in data modelling"
    re.compile(rf"{NUMBER}\s*\++{YEARS}", re.IGNORECASE),
    # "minimum 3-5 years", "at least 2 years in front-end development"
    re.compile(rf"(?:minimum|at least|min\.)\s*(?:of\s+)?{NUMBER}{RANGE_END}{YEARS}", re.IGNORECASE),
]
MAX_PLAUSIBLE_YEARS = 15  # larger numbers are usually company history, e.g. "20+ years in the industry"
MAX_YEARS = 2
MIN_DESCRIPTION_LENGTH = 200


def map_role(text):
    if not isinstance(text, str):
        return None
    for role, pattern in ROLE_RULES:
        if pattern.search(text):
            return role
    return None


def years_required(description):
    """The highest minimum number of years stated, or None if no years are stated."""
    minimums = []
    for pattern in YEARS_OF_EXPERIENCE:
        for match in pattern.finditer(description):
            if re.search(r"degree|diploma", match.group(0), re.IGNORECASE):
                continue  # e.g. "two year college degree or equivalent experience"
            value = match.group(1).lower()
            years = NUMBER_WORDS.get(value) or int(value)
            if years <= MAX_PLAUSIBLE_YEARS:
                minimums.append(years)
    return max(minimums) if minimums else None


def asks_for_little_experience(description):
    if SENIOR_DESCRIPTION.search(description):
        return False
    if FRESH_GRADUATE.search(description):
        return True
    years = years_required(description)
    return years is None or years <= MAX_YEARS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()

    postings = pd.read_csv(args.input_csv, low_memory=False)
    print(f"Raw rows {len(postings):,}")

    in_scope = (postings["category"] == ICT_CATEGORY) | postings["subcategory"].isin(RELATED_SUBCATEGORIES)
    postings = postings[in_scope]
    print(f"In scope (ICT and related subcategories) {len(postings):,}")

    titles = postings["job_title"]
    postings = postings[~titles.str.contains(SENIOR_TITLE) & ~titles.str.contains(INTERNSHIP_TITLE)]
    print(f"Entry-level titles, internships removed {len(postings):,}")

    postings = postings[~postings["job_title"].str.contains(EXCLUDED_TITLE)]
    print(f"Support, sales and training titles removed {len(postings):,}")

    # Match the title first, then JobStreet's role slug when no title rule matches
    by_title = postings["job_title"].map(map_role)
    by_slug = postings["role"].str.replace("-", " ").map(map_role)
    postings = postings.assign(role_title=by_title.fillna(by_slug))
    unmapped = postings[postings["role_title"].isna()]
    postings = postings[postings["role_title"].notna()]
    print(f"Mapped to a target role {len(postings):,} (by role slug: {(by_title.isna() & by_slug.notna()).sum():,})")

    postings = postings[postings["descriptions"].str.len() >= MIN_DESCRIPTION_LENGTH]
    print(f"Description of {MIN_DESCRIPTION_LENGTH}+ characters {len(postings):,}")

    postings = postings[postings["descriptions"].map(asks_for_little_experience)]
    print(f"Asks for {MAX_YEARS} years of experience or less {len(postings):,}")

    postings = postings.assign(
        listing_date=pd.to_datetime(postings["listingDate"], utc=True).dt.date,
        description_key=postings["descriptions"].str.lower().str.split().str.join(" "),
        company_key=postings["company"].str.lower().str.strip(),
    )
    # A repeated posting keeps its most recent copy
    postings = postings.sort_values("listing_date", ascending=False)
    postings = postings.drop_duplicates(["company_key", "description_key"])
    print(f"After removing duplicates {len(postings):,}")

    cleaned = postings.rename(columns={"descriptions": "description"})
    cleaned = cleaned[["job_id", "role_title", "job_title", "listing_date", "description"]].astype({"job_id": "int64"})
    cleaned.to_csv(args.output_csv, index=False)

    summary = cleaned.groupby("role_title").agg(
        postings=("job_id", "size"), earliest=("listing_date", "min"), latest=("listing_date", "max")
    )
    print("\nPostings per role")
    print(summary.sort_values("postings", ascending=False).to_string())

    print("\nMost common unmapped titles")
    print(unmapped["job_title"].str.lower().value_counts().head(20).to_string())


if __name__ == "__main__":
    main()