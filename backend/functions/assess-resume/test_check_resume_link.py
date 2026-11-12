"""Tests for the A1 level 3 link check. Run: python -m pytest inference"""

import pytest

from check_resume_link import apply_link_check


@pytest.mark.parametrize("level, text, pdf_links, expected", [
    # counts as a link to the work
    (2, "AI Content Detector - github.com/kelvin/ai-content-detector", (), 3),
    (2, "Source: https://github.com/kelvin/ai-content-detector).", (), 3),
    (2, "Live app: https://kerjaready.vercel.app", (), 3),
    (2, "Portfolio: kelvin.dev", (), 3),
    (2, "Website design and maintenance: www.lexingtoneyecare.org", (), 3),
    (2, "Demo on huggingface.co/spaces/kelvin/resume-rater", (), 3),
    (2, "Projects (links in PDF)", ["https://github.com/kelvin/ai-content-detector"], 3),
    # does not count
    (2, "GitHub: github.com/kelvin | LinkedIn: linkedin.com/in/kelvin", (), 2),
    (2, "Email: kelvin@gmail.com", (), 2),
    (2, "Acme Sdn Bhd (www.acme.com.my), Software Engineer Intern", (), 2),
    (2, "Built web apps with ASP.NET and Node.js", (), 2),
    (2, "Developed and customised the user interface in salesforce.com", (), 2),
    (2, "Lead Program Manager for corporate website www.riverbed.com", (), 2),
    (2, "Projects (links in PDF)", ["https://www.linkedin.com/in/kelvin"], 2),
    (2, "Projects (links in PDF)", ["https://kelvin.dev"], 2),  # unknown site without context
    # level 3 needs level 2 first
    (1, "github.com/kelvin/ai-content-detector", (), 1),
    (0, "github.com/kelvin/ai-content-detector", (), 0),
])
def test_apply_link_check(level, text, pdf_links, expected):
    assert apply_link_check(level, text, pdf_links)[0] == expected


def test_returns_the_link_used():
    level, link = apply_link_check(2, "Code: github.com/kelvin/ai-content-detector.")
    assert (level, link) == (3, "github.com/kelvin/ai-content-detector")