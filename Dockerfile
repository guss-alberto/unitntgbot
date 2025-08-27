# From example at: https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# Build app dependencies
FROM python:3.13.5-slim-bookworm AS builder

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
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY frontend ./frontend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --package ${PACKAGE}


# Copy app to runtime stage
FROM python:3.13.5-slim-bookworm
WORKDIR /app

# Install system dependencies, libcairo2 is installed only if the package is 'maps'
ARG PACKAGE
RUN apt-get update \
    && apt-get install -y --no-install-recommends dumb-init tzdata \
    && if [ "${PACKAGE:-}" = "maps" ]; then \
        apt-get install -y --no-install-recommends libcairo2; \
    fi \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
COPY backend/maps/src/maps/fonts/ /usr/local/share/fonts/

COPY --from=builder /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Set timezone to Rome so the time gets formatted correctly
ENV TZ=Europe/Rome

# https://github.com/Yelp/dumb-init
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Swap user to non-root
# USER nobody 

ENV PACKAGE=${PACKAGE}
CMD ["sh", "-c", "${PACKAGE}"]
