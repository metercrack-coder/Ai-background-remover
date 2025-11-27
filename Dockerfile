FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY app.py .
COPY index.html .
COPY Procfile .

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 10000

# Run
CMD gunicorn --bind 0.0.0.0:10000 --timeout 300 app:app
