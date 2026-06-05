FROM python:3.11-slim

WORKDIR /app

# pynput -> evdev needs Linux input headers to compile on slim images
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY dungeon_crawler/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY dungeon_crawler /app/dungeon_crawler

ENV PYTHONPATH=/app/dungeon_crawler
WORKDIR /app/dungeon_crawler

CMD ["python", "-m", "dungeon_crawler.main"]
