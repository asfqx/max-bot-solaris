FROM python:3.13-slim

WORKDIR /app

# системные зависимости (psycopg2 / asyncpg / alembic)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ставим uv
RUN pip install --no-cache-dir uv

# копируем только зависимости сначала (для кеша Docker)
COPY pyproject.toml uv.lock ./

# устанавливаем зависимости через uv (в .venv)
RUN uv sync --frozen --no-dev

# копируем код
COPY . .

# data dir
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data

# запуск через uv (ВАЖНО)
CMD ["uv", "run", "python", "main.py"]