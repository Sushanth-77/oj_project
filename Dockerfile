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
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Set working directory to where manage.py is located
WORKDIR /app/oj_project/oj_project

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Make build script executable (if needed)
RUN chmod +x /app/build.sh || true

# Set proper permissions
RUN chmod -R 755 /app && \
    chmod -R 777 /app/logs /app/media

# Run build commands from the correct directory
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

# Update the gunicorn command to run from the correct directory
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "oj_project.wsgi:application"]