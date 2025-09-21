FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY simple_transaction_checker.py .

# Create directory for state file
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV COUNT_FILE_PATH=/app/data/transaction_count.txt
ENV LOG_LEVEL=INFO

# Run the simple checker script
CMD ["python", "simple_transaction_checker.py"]
