FROM ubuntu:18.04
FROM python:latest

RUN python -m pip install --upgrade pip

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
RUN mkdir -v /notion_plugin
WORKDIR /notion_plugin
COPY . .

ENV PATH="${PATH}:/root/.poetry/bin"

RUN pip install --upgrade pip
RUN pip install setuptools
RUN poetry config virtualenvs.in-project true
RUN poetry install

RUN echo 'eval "$(direnv hook bash)"' > .bashrc
RUN curl -sfL https://direnv.net/install.sh | bash
RUN direnv allow .

RUN ls -lah
RUN "pwd"

RUN poetry run python app.py
