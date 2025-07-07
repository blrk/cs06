FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

# Copy app code
COPY big/ big/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "big.streamapp.wsgi:app", "--bind", "0.0.0.0:5000", "--timeout", "120"]