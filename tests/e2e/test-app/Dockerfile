FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install --no-cache-dir flask

# Copy application
COPY app.py .

# Expose port 8080
EXPOSE 8080

# Set PORT environment variable (can be overridden)
ENV PORT=8080

# Run the application
CMD ["python", "app.py"]
