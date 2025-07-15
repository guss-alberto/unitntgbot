# From example at: https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# Build app dependencies
FROM python:3.13.0-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.7.21 /uv /bin/
WORKDIR /app

ARG PACKAGE
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=backend,target=backend \
    --mount=type=bind,source=frontend,target=frontend \
    uv sync --locked --no-dev --no-install-workspace --package ${PACKAGE}

# Build app
COPY pyproject.toml uv.lock README.md ./
COPY backend ./backend
COPY frontend ./frontend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --package ${PACKAGE}


# Copy app to runtime stage
FROM python:3.13.0-slim-bookworm
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

ARG PACKAGE
ENV PACKAGE=${PACKAGE}
CMD ["sh", "-c", "${PACKAGE}"]
