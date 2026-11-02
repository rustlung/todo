# To-Do List

Черновая документация для локального запуска и проверки приложения.

## Требования

- Python 3.12

## Локальный запуск

В PowerShell из корня проекта:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

После запуска откройте `http://127.0.0.1:8000`.

SQLite-база по умолчанию будет создана в `data/todo.db`.

## Тесты

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

