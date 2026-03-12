FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask dbfread

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
