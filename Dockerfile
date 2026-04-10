FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl && apt-get clean

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 5000

CMD ["poetry", "run", "python", "app.py"]