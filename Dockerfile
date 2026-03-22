FROM python:3.12-slim
ARG CACHE_BUST=6
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt gunicorn
COPY . /app/
RUN python manage.py collectstatic --noinput
EXPOSE 8080
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:${PORT:-8080} myshop.wsgi:application"]
