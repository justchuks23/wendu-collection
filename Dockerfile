FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements /tmp/requirements
RUN pip install --no-cache-dir -r /tmp/requirements/development.txt
COPY . /app
EXPOSE 8000
