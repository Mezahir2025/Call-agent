# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies (needed for audio processing if we add ffmpeg later)
# RUN apt-get update && apt-get install -y ffmpeg

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the web service on container startup
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
