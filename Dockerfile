FROM ubuntu:24.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    cmake \
    libmagickwand-dev \
    python3 \
    python3-pip

# Use imei to install ImageMagick
RUN t=$(mktemp) && wget 'https://dist.1-2.dev/imei.sh' -qO "$t" && bash "$t" && rm "$t"

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for storing images
RUN mkdir -p /app/images

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (will be overridden in docker-compose)
CMD ["python", "app.py"] 