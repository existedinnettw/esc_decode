# Build stage
FROM python:3.12-alpine AS builder

# Set working directory
WORKDIR /app

# Install uv (modern Python package manager)
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY esc_decode/ ./esc_decode/

# Install dependencies using uv (production only)
RUN uv sync --frozen --no-dev

# Pre-compile Python bytecode for faster startup
RUN python -m compileall esc_decode/

# Production stage
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the pre-compiled application code
COPY --from=builder /app/esc_decode /app/esc_decode

# Activate virtual environment by setting PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Python optimizations
ENV PYTHONOPTIMIZE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the entrypoint to use python directly from venv
ENTRYPOINT ["python", "-m", "esc_decode"]