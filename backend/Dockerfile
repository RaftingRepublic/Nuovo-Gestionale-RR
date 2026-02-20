# Base Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Required for OpenCV, Paddle, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_fixed.txt .

# Install Python dependencies
# Use --no-cache-dir to keep image small
RUN pip install --no-cache-dir -r requirements_fixed.txt
# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create storage directory (if not mapped via volume, but good to have)
RUN mkdir -p storage/resources

# Expose port
EXPOSE 8000

# Run command
# 2 Workers should be enough for 1GB RAM and 15 users
CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "60"]
