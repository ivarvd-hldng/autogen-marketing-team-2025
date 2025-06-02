# Dockerfile voor AutoGen Marketing Team

FROM python:3.11-slim

WORKDIR /app

# Installeer systeemafhankelijkheden
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopieer requirements en installeer afhankelijkheden
COPY deployment/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de applicatiecode
COPY . .

# Standaard omgevingsvariabelen
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=8000

# Expose de poort waarop de applicatie draait
EXPOSE 8000

# Start de web applicatie
CMD ["gunicorn", "src.web.wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--log-file", "-"]