# Use python 3.12 slim image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose port for SSE
EXPOSE 7999

# Run server with SSE transport
CMD ["uv", "run", "python", "server.py"]

