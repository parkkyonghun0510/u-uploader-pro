# Use official Python runtime
FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install system dependencies, Firefox ESR, Geckodriver, and Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    xvfb \
    wget \
    curl \
    tar \
    bzip2 \
    ca-certificates \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    fonts-liberation \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Geckodriver directly to /usr/local/bin
RUN GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/' || echo "0.34.0") && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/v${GECKO_VERSION}/geckodriver-v${GECKO_VERSION}-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && \
    tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm -f /tmp/geckodriver.tar.gz

# Set working directory
WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set up entrypoint script permissions
RUN chmod +x /app/docker-entrypoint.sh

# Expose port for the dashboard / Web API
EXPOSE 8080

# Define data volume mount points
VOLUME ["/app/profiles", "/app/profile", "/app/logs", "/app/queue"]

# Set entrypoint to run Xvfb before the server
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command to run web application server
CMD ["python", "run.py"]
