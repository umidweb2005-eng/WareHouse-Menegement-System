# syntax=docker/dockerfile:1
# Multi-stage build for the donation bot.
# NOTE: not built in the design sandbox (network is integrations-only); this is
# the authoritative build definition for real environments.

FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
COPY src ./src
COPY migrations ./migrations
RUN pip install --upgrade pip && pip install .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Entrypoint decides: run migrations, then start the bot.
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
CMD ["run"]
