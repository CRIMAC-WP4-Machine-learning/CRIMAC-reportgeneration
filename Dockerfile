FROM python:3.8 as builder

RUN mkdir /install
WORKDIR /install

# Copy ca.cer (certificate authority) if it exists. Necessary in a SSL decrypt evironment.
COPY requirements.txt ca.cer* /

RUN apt-get update -y && \
    apt-get install -y git && \
    (test ! -f /ca.cer || git config --global http.sslCAInfo /ca.cer) && \
    (test ! -f /ca.cer || pip config set global.cert /ca.cer) && \
    pip install --prefix=/install -r /requirements.txt
RUN python -m pip install "dask[distributed]" --upgrade

FROM python:3.8-slim

ARG version_number
ARG commit_sha

ENV VERSION_NUMBER=$version_number
ENV COMMIT_SHA=$commit_sha

COPY --from=builder /install /usr/local
COPY reportgeneration /app/reportgeneration

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app

CMD ["python", "/app/reportgeneration/DockerMain.py"]
