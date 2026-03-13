# Desktop App

## Dev

1. Запусти фронт:
```bash
cd ../frontend
npm install
npm run dev
```

2. Запусти Electron:
```bash
cd ../desktop
npm install
npm run dev
```

## Build (Linux)
```bash
cd ../desktop
npm install
npm run build:frontend
npm run build:linux
```

Результат будет в `desktop/dist/`.

## Windows / macOS
Сборка выполняется на соответствующей ОС:
```bash
npm run build:win
npm run build:mac
```

## Windows build on Ubuntu (Wine)

1) Установить Wine:
```bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y wine64 wine32
```

2) Указать адрес API и токен для безлимита (вшиваются в билд):
```bash
export VITE_API_BASE_URL="http://83.222.10.35:8011"
export VITE_DESKTOP_TOKEN="ваш_токен"
```

3) Собрать:
```bash
cd ../desktop
npm install
npm run build:frontend
npm run build:win
```

Результат будет в `desktop/dist/`.

Примечания:
- `http://83.222.10.35:8011/docs` — это Swagger, базовый API URL: `http://83.222.10.35:8011`.
- Для безлимита на сервере нужно задать `DESKTOP_UNLIMITED_TOKEN` и включить CORS.
