
#
# Stage: staging
#
FROM python:3.10.9-slim as staging

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 
ENV \
    POETRY_VERSION=1.3.2 \
    POETRY_HOME="/opt/poetry" \ 
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 

# Install Poetry
RUN apt-get update \
    && apt-get install --no-install-recommends --assume-yes curl
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=${POETRY_HOME} POETRY_VERSION=${POETRY_VERSION} python3 - 
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Import project files
WORKDIR /src
COPY ./poetry.lock ./pyproject.toml ./
COPY ./app ./app

#
# Stage: development
#
FROM staging as development

# Install project in editable mode and with development dependencies
WORKDIR /src
RUN poetry install

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT [ "poetry", "run"]
CMD ["streamlit", "run", "./app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]