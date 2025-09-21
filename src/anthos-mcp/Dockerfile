FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV BANK_API_URL=http://userservice:8080

# Expose port (though MCP typically uses stdio)
EXPOSE 8080

# Run the MCP server
CMD ["python", "server.py"]