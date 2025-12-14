# Docker Setup Guide

This project is containerized using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update the values as needed.

2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000
   - Admin Panel: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000/admin

## Services

- **db**: PostgreSQL database
- **backend**: Django REST API
- **frontend**: React frontend (served via Nginx)

## Useful Commands

### Start services in background:
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f
```

### View logs for specific service:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Run migrations:
```bash
docker-compose exec backend python manage.py migrate
```

### Create superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Access backend shell:
```bash
docker-compose exec backend python manage.py shell
```

### Rebuild specific service:
```bash
docker-compose build backend
docker-compose build frontend
```

### Remove volumes (database data):
```bash
docker-compose down -v
```

## Development vs Production

### Development (default):
```bash
docker-compose up
```

### Production:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Environment Variables

See `.env.example` for all available environment variables.

**Important for production:**
- Set `DEBUG=False`
- Set a strong `SECRET_KEY`
- Update database credentials
- Set `VITE_API_BASE_URL` to your production API URL

## Troubleshooting

### Database connection errors:
- Ensure the database service is healthy: `docker-compose ps`
- Check database logs: `docker-compose logs db`

### Frontend can't connect to backend:
- Check `VITE_API_BASE_URL` in `.env`
- Ensure backend is running: `docker-compose ps backend`

### Port already in use:
- Change ports in `docker-compose.yml` if needed
- Or stop the conflicting service

