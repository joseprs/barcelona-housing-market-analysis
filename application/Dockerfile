FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY application/requirements-app.txt application/requirements-app.txt
RUN pip install --no-cache-dir -r application/requirements-app.txt

COPY application application
COPY src src
COPY models models

EXPOSE 8000

CMD ["uvicorn", "application.app.main:app", "--host", "0.0.0.0", "--port", "8000"]