# Document Anonymization Service

## Запуск (локально)

### Backend
```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://127.0.0.1:5173` и проксирует API на `http://127.0.0.1:8000`.

## Docker (prod)
```bash
docker compose up --build -d
```

- Приложение: `http://<IP>:8088` (через Nginx)
- Прямой backend: `http://<IP>:8000`

## Структура

```
backend/
  app/
  main.py
  requirements.txt
frontend/
  src/
  package.json
Dockerfile
docker-compose.yml
nginx.conf
```

## Ограничения
- до 10 документов в день на сессию
- до 5 файлов за одну мультизагрузку
