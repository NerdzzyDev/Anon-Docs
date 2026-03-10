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
