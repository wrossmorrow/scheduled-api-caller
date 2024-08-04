ARG PYTHON_VERSION=3.10-slim
ARG POETRY_VERSION=1.5.1

FROM python:${PYTHON_VERSION}

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get -y upgrade \
    && apt-get -y install --no-install-recommends curl python3-dev gcc libpq-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -y clean

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/etc/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=${POETRY_VERSION}

ENV POETRY_PATH="${POETRY_HOME}/bin/poetry"

# https://python-poetry.org/docs/master/#installation
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin && ln -s ${POETRY_PATH} && chmod +x ${POETRY_PATH}

COPY ./poetry.lock ./pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install -vvv --no-dev --no-root

COPY ./caller ./caller

ENTRYPOINT ["ddtrace-run", "python", "-m", "caller"]
