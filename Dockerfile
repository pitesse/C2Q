FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install \
      xdsl \
      qiskit \
      qiskit-aer \
      matplotlib \
      typing_extensions

COPY C2Q /app/C2Q
COPY tests /app/tests
COPY benchmarks_data /app/benchmarks_data
COPY README.md /app/README.md

CMD ["python", "-m", "C2Q", "tests/inputs/test_add.c"]
