FROM python:3.12-slim

WORKDIR /app

# Requirements from api subdir
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code and database configuration
COPY shared/ ./shared/
COPY database/ ./database/

# Copy api code
COPY api/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
