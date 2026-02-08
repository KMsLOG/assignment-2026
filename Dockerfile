# Use a Python 3.14 image
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the exact versions from uv.lock
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.14-slim

WORKDIR /app

# Copy the venv and application code from the builder
COPY --from=builder /app/.venv /app/.venv
COPY src /app/src

# Set environment path to use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
