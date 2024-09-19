# TODO API

Minimalistic RESTful API for task tracking

# How to build and run

## Build and run

```bash
docker compose up --build
```

and go to http://localhost:8000/docs

## Development

Prepare the database with applying scripts in migrations folder

### Set up the API

```bash
cd api
python -m venv venv
venv\Scripts\Activate.ps1  # venv/bin/activate
pip install -e ".[testing]"
cd src/todo_api
fastapi dev main.py
```

Run tests with 

```bash
cd ../..
pytest  # --cov-report html  # For HTML coverage report
```

# Notice

This project has the following dependencies
- `FastAPI`
- `pyjwt`
- `bcrypt`
- `SQLAlchemy`
- `psycopg`

- `ruff`
- `pytest`
- `pytest-cov`
