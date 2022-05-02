#!/usr/bin/env bash
poetry run flask db migrate && poetry run flask db upgrade && poetry run python app.py

