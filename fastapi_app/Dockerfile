# docker build -t t1 . && docker run --rm --volume -d -p "3000:3000" t1
FROM astral/uv:python3.12-bookworm-slim
WORKDIR /
# RUN apt update
# RUN apt install -y wget \
#   && apt install -y ffmpeg \
#   && apt install -y libsndfile1 \
#   && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# dev dependencies
ENV UV_NO_DEV=1
ENV UV_LINK_MODE=copy
# ENV UV_COMPILE_BYTECODE=1

EXPOSE 8000

COPY pyproject.toml uv.lock .python-version .
RUN --mount=type=cache,target=/root/.cache/uv \
uv sync --no-install-project

COPY ./code ./code
RUN uv sync --locked

# RUN pip install --no-cache-dir --upgrade spleeter
# RUN pip install --no-cache-dir --upgrade fastapi[standard]

# COPY docker_entry.sh /docker_entry.sh
# RUN chmod +x /docker_entry.sh
# CMD ["/docker_entry.sh"]

CMD ["uv", "run", "fastapi", "dev", "/app/code/main.py"]

