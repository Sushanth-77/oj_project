FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=oj_project.settings

WORKDIR /app

# Install system dependencies for compiling and running code
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

# Create necessary directories with proper permissions
RUN mkdir -p /app/inputs /app/outputs /app/static /app/media /app/logs /app/temp

# Create non-root user AFTER creating directories
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Set proper ownership and permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/temp /app/logs /app/media

# Create writable temp directory in /tmp for code execution
RUN mkdir -p /tmp/oj_temp && chmod 777 /tmp/oj_temp

# Switch to non-root user
USER appuser

# Set PATH to include user local bin
ENV PATH="/home/appuser/.local/bin:$PATH"

# Collect static files (handle gracefully if it fails)
RUN python manage.py collectstatic --noinput --clear || echo "Static files collection skipped"

EXPOSE 8000

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)" || exit 1

# Development command (override in docker-compose for production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]