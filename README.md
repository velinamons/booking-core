я змінила версію пайтон на 3.12, знобила новий інтерпритатор для poetry, poetry init

хіба ruff не включає в себе black? також я не хочу мати обмеження по великим файлам, також що таке --fix

# file: C:/Users/Vasyaka/PycharmProjects/booking-core/.pre-commit-config.yaml (text)
```
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
```
Чи можна взвгвлі не включати [build-system] та опис кожної tool для dev (або скоротити)

Чи можна не використовувати mypy?

# file: C:/Users/Vasyaka/PycharmProjects/booking-core/pyproject.toml (text)
```
[tool.poetry]
name = "booking-core"
version = "0.1.0"
description = "Calendar sessions management API"
authors = ["velinamons <velinamons@gmail.com>"]
readme = "README.md"
[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.23"}
asyncpg = "^0.29.0"
alembic = "^1.12.1"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
httpx = "^0.25.2"
black = "^23.12.0"
ruff = "^0.1.8"
pre-commit = "^3.6.0"
```
венв працює, тут все ок - Virtualenv Python:         3.12.10
