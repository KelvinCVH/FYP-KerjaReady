# Resume assessment function: ONNX rating model + A1 link check + B2 with LanguageTool
FROM public.ecr.aws/lambda/python:3.12

# Java 17 for LanguageTool (the base image's package manager is microdnf, also called dnf)
RUN dnf install -y java-17-amazon-corretto-headless && dnf clean all

# LanguageTool, downloaded at build time so it is never stored in git.
# The download site refuses Python's default User-Agent, so send a curl-style one.
ARG LT_VERSION=6.6
RUN python3 -c "import io, urllib.request, zipfile; req = urllib.request.Request('https://languagetool.org/download/LanguageTool-${LT_VERSION}.zip', headers={'User-Agent': 'curl/8.5.0'}); zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req).read())).extractall('/opt')" \
 && mv /opt/LanguageTool-${LT_VERSION} /opt/languagetool

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# rating_model.onnx, tokenizer.json and rating_config.json from export_rating_model_onnx.py
COPY model/ ${LAMBDA_TASK_ROOT}/model/
COPY onnx_rating_model.py check_resume_link.py rate_language_quality.py assess_resume.py ${LAMBDA_TASK_ROOT}/

CMD ["assess_resume.handler"]