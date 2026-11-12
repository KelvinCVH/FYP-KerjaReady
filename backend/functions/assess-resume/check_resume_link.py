"""A1 level 3 rule: a level 2 resume that links to the work itself is raised to level 3.

Rubric v1.0: level 3 needs level 2 plus a link to the work, meaning a code repository, a live demo or a
personal portfolio site. A GitHub profile link alone does not count. The model cannot learn this level
(the training resumes have almost no links), so this rule decides it.

Links are read from the resume text and, if the PDF parser provides them, from the PDF's hyperlinks.
"""

import re
from urllib.parse import urlparse

REPO_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}
# Hosts that serve deployed apps, demos and portfolio pages
DEMO_HOST_SUFFIXES = (".github.io", ".gitlab.io", ".vercel.app", ".netlify.app", ".herokuapp.com", ".streamlit.app",
                      ".onrender.com", ".pages.dev", ".web.app", ".firebaseapp.com", ".fly.dev", ".azurewebsites.net",
                      ".replit.app", ".glitch.me")
WORK_PATHS = {"huggingface.co": "spaces", "kaggle.com": "code"}  # host: first path part that marks a piece of work
PROFILE_HOSTS = {"linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com", "medium.com", "t.me", "wa.me"}
# Any other site counts only when the text right before it says it is the candidate's work
WORK_WORDS = re.compile(r"\b(portfolio|demo|live|deployed|hosted|built|build|developed|designed|design|created)\b", re.I)
# A bare domain with no path ("salesforce.com") is usually a product name, so it needs a label right before it
LABEL_BEFORE = re.compile(r"\b(portfolio|demo|live|website|site)\s*[:|\-]?\s*$", re.I)

URL_PATTERN = re.compile(
    r"(?<![@\w.])(?:https?://\S+|www\.\S+|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|io|app|dev|org|net|my|co|ai|me|site|tech|page)(?:/\S*)?)",
    re.I)


def find_links(text):
    """URL-like tokens in the text, with trailing punctuation removed."""
    return [m.group(0).rstrip(".,;:)]}'\"") for m in URL_PATTERN.finditer(text or "")]


def _parts(url):
    parsed = urlparse(url if re.match(r"https?://", url, re.I) else "http://" + url)
    host = parsed.netloc.lower().split(":")[0].removeprefix("www.")
    path = [p for p in parsed.path.split("/") if p]
    return host, path


def is_work_link(url, context=""):
    """True if the URL points at the work itself; context is the text just before the URL."""
    bare = not re.match(r"(https?://|www\.)", url, re.I)
    host, path = _parts(url)
    if host in REPO_HOSTS:
        return len(path) >= 2  # owner/repository; a profile has one part
    if host == "gist.github.com":
        return len(path) >= 2
    if host.endswith(DEMO_HOST_SUFFIXES):
        return True
    if host in WORK_PATHS:
        return len(path) >= 3 and path[0] == WORK_PATHS[host]
    if host in PROFILE_HOSTS or not host or "." not in host:
        return False
    if bare and url != url.lower():
        return False  # technology names such as ASP.NET look like domains; written web addresses are lower case
    if bare and not path:
        return bool(LABEL_BEFORE.search(context))
    return bool(WORK_WORDS.search(context))


def apply_link_check(a1_level, text, pdf_links=()):
    """Return (A1 level, the link that justified level 3 or None)."""
    if a1_level != 2:
        return a1_level, None
    for m in URL_PATTERN.finditer(text or ""):
        url = m.group(0).rstrip(".,;:)]}'\"")
        line_start = text.rfind("\n", 0, m.start()) + 1
        context = text[max(line_start, m.start() - 80):m.start()]
        if is_work_link(url, context):
            return 3, url
    for url in pdf_links:
        # A hyperlink without visible text has no context, so only repository and demo hosts count
        if is_work_link(url):
            return 3, url
    return a1_level, None