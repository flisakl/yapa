# What is YAPA?

YAPA stands for Yet Another Productivity App.

This repository is just an django-ninja API.

## How to run

There are couple of options, choose one that suits you best.

### Docker

> [!NOTE]
> This one uses PostgreSQL and Redis

...

### Virtual environment

Virtual environment and project setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python manage.py migrate
```

Start development server:
```bash
python manage.py runserver
```
