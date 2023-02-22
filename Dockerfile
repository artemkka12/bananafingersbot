FROM python:3.10-slim

WORKDIR /code

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.3.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

COPY poetry.lock pyproject.toml /code/

RUN pip install "poetry==$POETRY_VERSION"
RUN poetry install --no-root

COPY .. /code/

EXPOSE 8000

CMD ["bash", "./startup.sh"]