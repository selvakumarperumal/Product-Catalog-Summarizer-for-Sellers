# Dockerfile for the application
FROM python:3.13-slim AS base

# Set the working directory
WORKDIR ProductCatalogSummarizer

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Development stage
FROM base AS dev

# In development, we will mount the app directory as a volume
# so we don't need to copy the app files here.
# This allows for live reloading during development.

# Expose the port for the application
EXPOSE 8000

# Command to run the application in development mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Production stage
FROM base AS prod

# Copy the application code
COPY app/ ./app/

# Expose the port for the application
EXPOSE 8000

# Command to run the application in production mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]