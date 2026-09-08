FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Tesseract OCR
RUN apt-get update \
    && apt-get install -y \
       tesseract-ocr \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY backend/ .

RUN mkdir -p /app/uploads

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]