FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and workflow files
COPY telegram_bot.py .
COPY flux_workflow_simple.json .
COPY healthcheck.sh .

# Create output directory
RUN mkdir -p /app/outputs

# Make healthcheck script executable
RUN chmod +x /app/healthcheck.sh

# Run as non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "telegram_bot.py"]
