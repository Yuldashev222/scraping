FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip \
 && pip install --prefer-binary -r /requirements.txt

COPY ./src .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
