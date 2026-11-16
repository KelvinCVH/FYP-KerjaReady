"""
POST /candidate/resumes: start a resume upload for the signed-in candidate.

Saves the resume row (status: uploading) and returns a presigned POST, so the browser
sends the PDF straight to S3. S3 itself rejects files over 5 MB or not sent as a PDF.
"""

import base64
import json
import os
import uuid

import boto3
from botocore.config import Config
from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

MAX_BYTES = 5 * 1024 * 1024
UPLOAD_SECONDS = 300
INVALID_FILE = {"message": "Choose a PDF file."}

_s3 = None


def _client():
    """Regional endpoint, so the browser posts to the bucket's own region."""
    global _s3
    if _s3 is None:
        region = os.environ["AWS_REGION"]
        _s3 = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
    return _s3


def read_file_name(event):
    """The PDF's file name from the body, or None when the body or name is not valid."""
    try:
        body = event.get("body") or ""
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        body = json.loads(body)
    except ValueError:
        return None
    if not isinstance(body, dict) or not isinstance(body.get("file_name"), str):
        return None

    file_name = body["file_name"].strip()
    if len(file_name) > 255 or not file_name.lower().endswith(".pdf"):
        return None
    return file_name


@api_handler
def handler(event, user):
    file_name = read_file_name(event)
    if file_name is None:
        return 400, INVALID_FILE

    s3_key = f"resumes/{user['user_id']}/{uuid.uuid4()}.pdf"
    rows = run_query(
        "INSERT INTO resumes (candidate_id, file_name, s3_key) "
        "VALUES (CAST(:user_id AS uuid), :file_name, :s3_key) RETURNING resume_id",
        [
            {"name": "user_id", "value": {"stringValue": user["user_id"]}},
            {"name": "file_name", "value": {"stringValue": file_name}},
            {"name": "s3_key", "value": {"stringValue": s3_key}},
        ],
    )

    upload = _client().generate_presigned_post(
        Bucket=os.environ["RESUME_BUCKET_NAME"],
        Key=s3_key,
        Fields={"Content-Type": "application/pdf"},
        Conditions=[{"Content-Type": "application/pdf"}, ["content-length-range", 1, MAX_BYTES]],
        ExpiresIn=UPLOAD_SECONDS,
    )
    return 201, {"resume_id": rows[0]["resume_id"], "upload": upload}