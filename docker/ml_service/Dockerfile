FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy Poetry files
# Файлы находятся в корне контекста сборки (../ml_service)
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install in the same container
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY app /app/ml_service/app
COPY models /app/ml_service/models
COPY data /app/ml_service/data

# Set environment variables
ENV PYTHONPATH=/app
ENV MODEL_DIR=/app/ml_service/models
ENV DATA_DIR=/app/ml_service/data

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "ml_service.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
