FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the application port
EXPOSE 9000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "9000"]