FROM python:3.11-slim

WORKDIR /app

# Proxy settings for corporate network (HTTP only - HTTPS proxy commented out)
ENV http_proxy='http://165.225.206.24:10299' \
    HTTP_PROXY='http://165.225.206.24:10299'
    # https_proxy='http://165.225.206.24:10299' \
    # HTTPS_PROXY='http://165.225.206.24:10299' \
    # no_proxy='localhost,127.0.0.1,backend,frontend,nginx'

# Copy Zscaler certificate and update CA certificates
COPY ./zscaler.crt /usr/local/share/ca-certificates/
RUN apt-get update && \
    apt-get install -y ca-certificates curl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/* || true

# Install Python dependencies
COPY ./backend/requirements_fastapi.txt requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy backend code
COPY ./backend .

# Create directories for files and set permissions
RUN mkdir -p attachments data logs && \
    chmod -R 777 /app/data /app/logs /app/attachments

# Expose port 8000
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]