FROM python:3.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /orders-management-system
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
