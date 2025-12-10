# Base image with Python 3.12
FROM python:3.12-slim

# Install system dependencies
# - fonts-wqy-microhei: Chinese font for PDF generation
# - gcc, libc-dev: Build tools for some python packages
# - make, wget: Build tools for TA-Lib
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    fontconfig \
    gcc \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr && \
  make && \
  make install && \
  cd .. && \
  rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (Render sets the PORT env var, default is 10000)
EXPOSE 10000

# Run the application with Gunicorn
# Listen on 0.0.0.0 with the port defined in environment variable
# Increase timeout to 120s to allow for slow data fetching
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 120 web_app:app
