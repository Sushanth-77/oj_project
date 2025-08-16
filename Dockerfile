FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/oj_project"
ENV DJANGO_SETTINGS_MODULE=oj_project.settings

WORKDIR /app

# Install system dependencies INCLUDING COMPILERS
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk \
    nodejs \
    npm \
    build-essential \
    libpq-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Verify compilers are installed
RUN gcc --version && g++ --version && javac -version && node --version

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Make scripts executable
RUN chmod +x build.sh startup.sh

# Create directories
RUN mkdir -p staticfiles media logs

EXPOSE 8000

CMD ["./startup.sh"]