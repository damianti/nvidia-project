FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port 8080 (standard Cloud Run port)
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV SERVICE_NAME=example-service
ENV ENV=production

# Run the application
CMD ["python", "app.py"]
