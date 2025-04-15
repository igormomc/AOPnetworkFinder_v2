# Use Debian 12 (Bookworm) as the base image
FROM debian:bookworm-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3.11-dev \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment inside a named volume path
RUN python3 -m venv /venv

# Upgrade pip and setuptools to secure versions
RUN /venv/bin/python -m pip install --upgrade pip "setuptools>=65.5.1"

# Install Python dependencies
COPY requirements.txt .
RUN /venv/bin/python -m pip install --no-cache-dir -r requirements.txt

# Install watchdog
RUN /venv/bin/python -m pip install watchdog

# Add a non-root user and switch to it
RUN useradd -m myuser
USER myuser

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Command to run the app using watchmedo
CMD ["/venv/bin/watchmedo", "auto-restart", "--directory=.", "--pattern=*.py", "--recursive", "--", "/venv/bin/gunicorn", "--reload", "-w", "4", "-b", ":8000", "--timeout", "120", "run:app"]

# This works to run on windows
# CMD ["/venv/bin/gunicorn", "--reload", "-w", "1", "-b", ":8000", "--timeout", "120", "--log-level", "debug", "run:app"]
