# Python + minimal Node to allow using cline in-container (Linux target)
FROM python:3.11-slim

ARG APP_USER=appuser
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps, Node/npm (for optional cline), then clean cache
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m ${APP_USER}
WORKDIR /app

# Python deps first for better layering
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Project files
COPY . .

USER ${APP_USER}
EXPOSE 8000

# Default command: FastAPI via uvicorn
CMD ["uvicorn", "services.api:app", "--host", "0.0.0.0", "--port", "8000"]
