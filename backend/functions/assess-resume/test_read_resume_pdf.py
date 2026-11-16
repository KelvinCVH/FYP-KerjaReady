import pytest

from read_resume_pdf import UnreadablePdf, read_resume_pdf

LINES = [
    "Software Engineering Intern, Example Sdn Bhd, 2025",
    "Built a REST API in Python and FastAPI for 2,000 daily users",
    "Reduced page load time by 40% by caching database queries",
    "Wrote unit tests with pytest and set up GitHub Actions for the team",
    "Bachelor of Computer Science, Asia Pacific University, 2026",
]


def make_pdf(lines=(), link=None):
    """A one-page PDF with the given text lines and an optional hyperlink."""
    content = "BT /F1 11 Tf 72 760 Td 14 TL " + " ".join(f"({line}) Tj T*" for line in lines) + " ET"
    annots = " /Annots [6 0 R]" if link else ""
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R{annots} >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
    ]
    if link:
        objects.append(f"<< /Type /Annot /Subtype /Link /Rect [72 700 200 720] /A << /S /URI /URI ({link}) >> >>")
    pdf = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    pdf += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return pdf


def test_reads_text_and_hyperlinks():
    text, links = read_resume_pdf(make_pdf(LINES, link="https://github.com/kelvin/kerjaready"))
    assert "Reduced page load time by 40%" in text
    assert links == ["https://github.com/kelvin/kerjaready"]


def test_pdf_without_links_gives_an_empty_list():
    _, links = read_resume_pdf(make_pdf(LINES))
    assert links == []


@pytest.mark.parametrize("data", [b"PK\x03\x04 a .docx file", b"ID3 an .mp3 file", b"", b"%PDF-1.4\nnot really a pdf"])
def test_files_that_are_not_readable_pdfs(data):
    with pytest.raises(UnreadablePdf) as error:
        read_resume_pdf(data)
    assert error.value.reason == "not_pdf"


@pytest.mark.parametrize("lines", [(), ("Kelvin Chin",)])
def test_scanned_or_almost_empty_pdf_has_no_text(lines):
    with pytest.raises(UnreadablePdf) as error:
        read_resume_pdf(make_pdf(lines))
    assert error.value.reason == "no_text"