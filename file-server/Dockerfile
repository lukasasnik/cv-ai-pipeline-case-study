FROM python:3.12-slim

WORKDIR /app

# Requirements from file-server subdir
COPY file-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ ./shared/

# Copy file-server code
COPY file-server/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
