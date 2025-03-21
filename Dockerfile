FROM python:3.12-slim

# Install ffmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory to /app
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script
COPY /app /app

# Run the app
CMD ["python", "-u", "main.py"]