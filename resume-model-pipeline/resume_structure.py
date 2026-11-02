"""Rebuild entries and bullet lines from a flattened resume.

A Python port of structureResume() in labelling_tool.html, so the LLM labeller
sees the same "Readable view" a human labeller sees. The split is a heuristic:
it can merge two jobs or leave a job title at the end of the previous entry.
"""

import re

RESP_RE = re.compile(r"(?:Roles?\s*(?:and|&)\s*Responsibilities|Responsibilities|Duties)\s*:", re.I)
ENV_LAST_RE = re.compile(r"(?:Environment|Technologies(?: Used)?|Tools(?: Used)?|Tech(?:nology)? Stack)\s*:", re.I)
SECTION_RE = re.compile(
    r"(?<![A-Z])\s(?=(?:PROFESSIONAL SUMMARY|SUMMARY|OBJECTIVE|TECHNICAL SKILLS|SKILLS|PROFESSIONAL EXPERIENCE|"
    r"WORK EXPERIENCE|EXPERIENCE|EDUCATION|CERTIFICATIONS?|ACADEMIC|TRAINING|PROJECTS?)\b)"
)
TAIL_RE = re.compile(r"\b(?:EDUCATION|ACADEMIC|CERTIFICATIONS?|TRAINING)\b")
SKILL_GROUP_SPLIT = re.compile(r"\s(?=[A-Z][A-Za-z/&().\- ]{1,28}:\s)")
VERBS = (
    "Developed|Designed|Created|Implemented|Involved|Responsible|Worked|Used|Using|Performed|Prepared|Managed|"
    "Configured|Installed|Wrote|Written|Built|Tested|Analyzed|Analysed|Participated|Coordinated|Maintained|Provided|"
    "Supported|Conducted|Gathered|Interacted|Monitored|Migrated|Converted|Generated|Extensively|Utilized|Utilised|"
    "Assisted|Led|Collaborated|Documented|Reviewed|Updated|Upgraded|Troubleshot|Troubleshooting|Creating|Developing|"
    "Designing|Writing|Working|Preparing|Performing|Configuring|Installing|Maintaining|Providing|Supporting|"
    "Monitoring|Analyzing|Analysing|Coordinating|Interacting|Attending|Reporting|Ensured|Ensuring|Resolved|"
    "Identified|Defined|Delivered|Deployed|Automated|Optimized|Optimised|Reduced|Improved|Increased|Achieved|Worked|"
    "Handled|Executed|Executing|Scheduled|Loaded|Extracted|Transformed|Modified|Enhanced|Facilitated|Trained|"
    "Mentored|Researched|Proposed|Presented|Established|Integrated|Administered|Planned"
)
VERB_SPLIT = re.compile(rf"(?<=[a-z0-9)%\]])\s+(?=(?:{VERBS})\b)")
SENTENCE_SPLIT = re.compile(r"(?<=[.;!?])\s+(?=[A-Z(])")
SUBHEAD_SPLIT = re.compile(r"\s(?=(?:Project(?: Name)?|Client|Role|Description)\s*:)")
SENTENCE_END = re.compile(r"[.;]\s+")


def to_lines(s):
    out = []
    for p in SENTENCE_SPLIT.split(s):
        for q in SUBHEAD_SPLIT.split(p):
            out.extend(VERB_SPLIT.split(q))
    return [p.strip() for p in out if len(p.strip()) > 1]


def _entry_start(text, resp_index, prev_end):
    start = max(prev_end, resp_index - 250)
    seg = text[start:resp_index]
    ci = seg.rfind("Confidential")
    if ci >= 0:
        # a header can contain "Confidential" twice (company and client); take the earlier one if close by
        earlier = seg.rfind("Confidential", 0, ci - 1 + len("Confidential")) if ci > 0 else -1
        if earlier >= 0 and earlier != ci and ci - earlier < 90:
            ci = earlier
        return start + ci
    ends = list(SENTENCE_END.finditer(seg))
    return start + ends[-1].end() if ends else start


def structure_resume(text):
    """Return {"preamble", "entries": [{"header", "lines", "env"}], "tail"}, or None if no entries are found."""
    marks = list(RESP_RE.finditer(text))
    if not marks:
        return None
    starts = []
    for k, m in enumerate(marks):
        prev_end = marks[k - 1].end() if k else 0
        starts.append(_entry_start(text, m.start(), prev_end))
    entries, tail = [], ""
    for k, m in enumerate(marks):
        body_start = m.end()
        end = starts[k + 1] if k + 1 < len(marks) else len(text)
        if k == len(marks) - 1:
            tails = list(TAIL_RE.finditer(text, body_start))
            if tails:
                end = tails[-1].start()
                tail = text[end:]
        body = text[body_start:end]
        envs = list(ENV_LAST_RE.finditer(body))
        env_at = envs[-1].start() if envs else -1
        entries.append({
            "header": text[starts[k]:m.start()].strip(),
            "lines": to_lines(body[:env_at] if env_at >= 0 else body),
            "env": body[env_at:].strip() if env_at >= 0 else "",
        })
    return {"preamble": text[:starts[0]].strip(), "entries": entries, "tail": tail.strip()}


def block_lines(s):
    out = []
    for part in SECTION_RE.split(s):
        if re.match(r"^(?:TECHNICAL SKILLS|SKILLS)", part.strip()):
            out.extend(SKILL_GROUP_SPLIT.split(part))
        else:
            out.extend(to_lines(part))
    return [p.strip() for p in out if p.strip()]


def readable_view(text):
    """Plain-text version of the tool's Readable view. Returns (view, detected_entry_count)."""
    s = structure_resume(text)
    if s is None:
        return "NO ENTRIES DETECTED (shown as sentences)\n" + "\n".join(f"- {l}" for l in to_lines(text)), 0
    parts = []
    if s["preamble"]:
        parts.append("SUMMARY AND SKILLS (not entries)\n" + "\n".join(f"- {l}" for l in block_lines(s["preamble"])))
    for i, e in enumerate(s["entries"], 1):
        block = [f"ENTRY {i}: {e['header'] or '(no header found)'}"] + [f"- {l}" for l in e["lines"]]
        if e["env"]:
            block.append(f"[Environment line] {e['env']}")
        parts.append("\n".join(block))
    if s["tail"]:
        parts.append("EDUCATION AND OTHER (not entries)\n" + "\n".join(f"- {l}" for l in block_lines(s["tail"])))
    return "\n\n".join(parts), len(s["entries"])