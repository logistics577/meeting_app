# -----------------------------
# Base Image
# -----------------------------
FROM python:3.10-slim

# -----------------------------
# Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Install system dependencies (optional)
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Copy project files
# -----------------------------
COPY . /app

# -----------------------------
# Install Python dependencies
# -----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Expose Port
# -----------------------------
EXPOSE 9080

# -----------------------------
# Environment variables
# -----------------------------
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Run the server
# -----------------------------
CMD ["python3", "main.py"]
