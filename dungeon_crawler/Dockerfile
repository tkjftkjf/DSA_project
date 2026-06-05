FROM python:3.11-slim

WORKDIR /app

COPY dungeon_crawler/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY dungeon_crawler /app/dungeon_crawler

CMD ["python", "-m", "dungeon_crawler.main"]
