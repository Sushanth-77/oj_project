FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=oj_project.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    curl \
    wget \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/inputs /app/outputs /app/static /app/media /app/logs /app/temp

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Set proper ownership and permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/temp /app/logs /app/media

# Create temp directory for code execution
RUN mkdir -p /tmp/oj_temp && chmod 777 /tmp/oj_temp

# Switch to non-root user
USER appuser

# Run Django setup commands
RUN python manage.py collectstatic --noinput --clear || echo "Static files collection skipped"
RUN python manage.py migrate --noinput || echo "Migration skipped"

EXPOSE 8000

# Simple health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]