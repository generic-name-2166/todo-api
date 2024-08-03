# TODO API

Minimalistic RESTful API for task tracking

# How to build and run

## Build and run

```bash
# TODO
```

and go to http://localhost:8000

## Development

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # venv/bin/activate
pip install -e ".[testing]"
cd src/todo_api
fastapi dev main.py
```

# Notice

This project uses the following dependencies
- `FastAPI`
