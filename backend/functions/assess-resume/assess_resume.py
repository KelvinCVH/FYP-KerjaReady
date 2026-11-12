"""Lambda handler: rate a resume on A1, A2, A3 (ONNX model, A1 link check) and B2 (LanguageTool).

Event:   {"text": "<resume text>", "pdf_links": ["https://...", ...]}   (pdf_links is optional)
Returns: {"a1": 0-3, "a2": 0-3, "a3": 0-3, "b2": 1-3, "a1_work_link": url or null,
          "b2_errors": [{"text", "rule", "message"}, ...], "model_version": "<training job>"}

LanguageTool runs as a local Java server inside the same container. It is started in the background
when the container starts (Lambda allows 10 s for that phase) and the first request waits until it is ready.
"""

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import rate_language_quality as language_quality
from check_resume_link import apply_link_check
from onnx_rating_model import OnnxRatingModel

MODEL_DIR = Path(os.environ.get("MODEL_DIR", Path(__file__).resolve().parent / "model"))
LT_DIR = Path(os.environ.get("LANGUAGETOOL_DIR", "/opt/languagetool"))
LT_PORT = int(os.environ.get("LANGUAGETOOL_PORT", "8081"))
LT_BASE = f"http://localhost:{LT_PORT}/v2"
LT_START_TIMEOUT = 90

model = OnnxRatingModel(MODEL_DIR)
_languagetool = None


def start_languagetool():
    """Start the bundled LanguageTool server if it is not running. Without the bundle (local development),
    a server started by hand on LANGUAGETOOL_PORT is used instead."""
    global _languagetool
    jar = LT_DIR / "languagetool-server.jar"
    if not jar.exists() or (_languagetool is not None and _languagetool.poll() is None):
        return
    _languagetool = subprocess.Popen(
        ["java", "-Xmx1g", "-Duser.home=/tmp", "-cp", str(jar), "org.languagetool.server.HTTPServer", "--port", str(LT_PORT)],
        cwd="/tmp", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_languagetool(timeout=LT_START_TIMEOUT):
    deadline = time.time() + timeout
    while True:
        try:
            urllib.request.urlopen(f"{LT_BASE}/languages", timeout=2)
            return
        except OSError:
            if time.time() > deadline:
                raise RuntimeError(f"LanguageTool did not answer on port {LT_PORT} within {timeout} s")
            time.sleep(0.5)


start_languagetool()  # in the background; the init phase continues while Java starts


def handler(event, context=None):
    text = (event or {}).get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("event.text must be a non-empty string with the resume text")
    started = time.time()

    levels = model.rate(text)
    a1, work_link = apply_link_check(levels["a1"], text, (event or {}).get("pdf_links") or [])

    start_languagetool()
    wait_for_languagetool()
    b2, b2_errors = language_quality.rate_b2(text, url=f"{LT_BASE}/check")

    result = {"a1": a1, "a2": levels["a2"], "a3": levels["a3"], "b2": b2, "a1_work_link": work_link,
              "b2_errors": b2_errors, "model_version": model.version}
    # log ratings and timing only, never the resume text
    print(json.dumps({"ratings": {k: result[k] for k in ("a1", "a2", "a3", "b2")}, "seconds": round(time.time() - started, 2)}))
    return result