FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Make build script executable
RUN chmod +x /app/build.sh

# Set proper permissions
RUN chmod -R 755 /app

# Set the Python path and Django settings
ENV PYTHONPATH="/app/oj_project:$PYTHONPATH"
ENV DJANGO_SETTINGS_MODULE=oj_project.settings

WORKDIR /app/oj_project/oj_project

# Force create migrations and migrate during build (using SQLite first)
RUN python manage.py makemigrations --settings=oj_project.build_settings
RUN python manage.py migrate --settings=oj_project.build_settings
RUN python manage.py collectstatic --noinput --settings=oj_project.build_settings

EXPOSE 8000

# Copy startup script
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

CMD ["/app/startup.sh"]