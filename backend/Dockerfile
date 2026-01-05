FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy entire project
COPY . /app

# Make it executable
RUN sed -i 's/\r$//' entrypoint.sh
RUN chmod +x entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV ENVIRONMENT=development

ENTRYPOINT ["sh", "entrypoint.sh"]