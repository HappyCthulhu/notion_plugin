#!/usr/bin/env bash
#poetry run flask db stamp head || poetry run flask db migrate || poetry run flask db upgrade || poetry run python app.py
poetry run flask db stamp head 
poetry run flask db migrate 
poetry run flask db upgrade 
poetry run python app.py
