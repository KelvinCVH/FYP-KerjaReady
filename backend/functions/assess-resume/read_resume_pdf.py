"""Read an uploaded resume PDF: its text, and the web links behind its hyperlinks.

A link such as "GitHub" in a PDF often hides its address, so the addresses are read from the
PDF's link annotations and passed to the A1 link check as pdf_links.
"""

import io

from pypdf import PdfReader

MAX_PAGES = 10  # a resume is a few pages; this bounds the time for very long files
MIN_TEXT_CHARACTERS = 200  # less than this is treated as a scanned PDF with no readable text


class UnreadablePdf(Exception):
    """reason is "not_pdf" (not a PDF, or damaged) or "no_text" (scanned or password-protected)."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _resolve(value):
    return value.get_object() if hasattr(value, "get_object") else value


def _page_links(page):
    for annotation in _resolve(page.get("/Annots")) or []:
        action = _resolve(_resolve(annotation).get("/A"))
        uri = _resolve(action.get("/URI")) if action else None
        if isinstance(uri, bytes):
            uri = uri.decode("latin-1")
        if isinstance(uri, str) and uri.strip():
            yield uri.strip()


def read_resume_pdf(data):
    """(text, links) from the PDF bytes, or UnreadablePdf."""
    if b"%PDF-" not in data[:1024]:
        raise UnreadablePdf("not_pdf")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    raise UnreadablePdf("no_text")
            except UnreadablePdf:
                raise
            except Exception as error:
                raise UnreadablePdf("no_text") from error
        pages = reader.pages[:MAX_PAGES]
        # PostgreSQL text cannot hold NUL characters, which some PDFs produce
        text = "\n".join(page.extract_text() or "" for page in pages).replace("\x00", "")
        links = list(dict.fromkeys(link for page in pages for link in _page_links(page)))
    except UnreadablePdf:
        raise
    except Exception as error:
        print(f"PDF could not be read: {type(error).__name__}")  # the type only, never the content
        raise UnreadablePdf("not_pdf") from error

    if len(text.strip()) < MIN_TEXT_CHARACTERS:
        raise UnreadablePdf("no_text")
    return text, links