FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["functions-framework", "--target=proxy_sagas", "--port=8080"]
