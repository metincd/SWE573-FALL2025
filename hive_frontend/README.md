# The Hive - Frontend

React + TypeScript + Vite + Tailwind CSS ile geliştirilmiş frontend uygulaması.

## Kurulum

```bash
npm install
```

## Geliştirme

```bash
npm run dev
```

Uygulama `http://localhost:5173` adresinde çalışacak.

## Backend Bağlantısı

`.env` dosyasında `VITE_API_BASE_URL` değişkenini backend API adresine göre ayarlayın:

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Build

```bash
npm run build
```

## Özellikler

- ✅ React Router ile sayfa yönlendirme
- ✅ JWT Authentication
- ✅ React Query ile API state yönetimi
- ✅ Tailwind CSS ile styling
- ✅ Axios ile API istekleri
