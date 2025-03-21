# filepath: Dockerfile
FROM python:3.12-slim

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Create group and user with the specified UID/GID.
RUN addgroup --gid ${GROUP_ID} appgroup && \
    adduser --disabled-password --gecos "" --uid ${USER_ID} --ingroup appgroup appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Change ownership and run as appuser.
RUN chown -R appuser:appgroup /app
USER appuser

CMD ["python", "-u", "app/main.py"]