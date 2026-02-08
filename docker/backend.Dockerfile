# backend.Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy only packaging files first to leverage Docker layer caching
COPY pyproject.toml /app/
COPY src /app/src

# Install *as a package*
RUN pip install .

EXPOSE 8081
CMD ["uvicorn", "sqlmate.backend.main:app", "--host", "0.0.0.0", "--port", "8081"]