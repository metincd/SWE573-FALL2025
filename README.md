# The Hive - Community Time Banking Platform

## Overview

The Hive is a community-driven time banking platform designed to facilitate service exchange and strengthen local community bonds. The platform enables users to offer and request services using a virtual currency called Time Bank Hours (TBH), where one hour of service equals one TBH. By replacing monetary transactions with time-based exchanges, The Hive promotes reciprocity, mutual aid, and community solidarity.

This project was developed as part of the SWE573 Software Development Practice course at Boğaziçi University, Fall 2025.

## Live Demo

The application is currently deployed on AWS EC2 and accessible at:

**Live Application**: [http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:3000/](http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:3000/)

The platform is fully functional and ready for use. You can register an account, explore services on the interactive map, and experience all features of the time banking system.

## Key Features

### Service Exchange
- **Service Offers and Needs**: Users can create service posts (offers or needs) with detailed descriptions, estimated time requirements, and location information
- **Interactive Map**: Geographic visualization of all services using Leaflet maps with color-coded markers for offers (green) and needs (blue)
- **Service Requests**: Users can request services from others and manage the exchange process through a dedicated dashboard
- **Two-Party Confirmation**: Both service provider and recipient must confirm completion before time credits are transferred

### Time Banking System
- **Virtual Currency**: Time Bank Hours (TBH) system where 1 hour of service = 1 TBH
- **Initial Balance**: New users receive 3 TBH upon registration to encourage participation
- **Automatic Transfers**: Time credits are automatically transferred upon mutual service completion
- **Transaction History**: Complete audit trail of all time transactions with detailed records

### Community Features
- **Forums**: Community discussion threads organized by interests and topics
- **Service Discussions**: Each service has an associated public discussion thread
- **Private Messaging**: Secure messaging system for coordinating service details
- **Thank You Notes**: Users can express gratitude for completed services
- **Reviews and Ratings**: Comprehensive review system with ratings and helpful votes

### Moderation and Administration
- **Reporting System**: Users can report inappropriate content with multiple reason categories
- **Admin Panel**: Comprehensive administrative dashboard with system statistics and moderation tools
- **User Management**: Ban and suspension capabilities with automatic expiration handling
- **Content Moderation**: Administrators can remove posts, ban users, and manage reports

## Technology Stack

### Backend
- **Framework**: Django 4.2.25
- **API**: Django REST Framework 3.16.1
- **Authentication**: JWT (JSON Web Tokens) via djangorestframework-simplejwt
- **Database**: PostgreSQL 15
- **Geocoding**: OpenStreetMap Nominatim integration
- **File Storage**: Local media storage with support for avatars and service images

### Frontend
- **Framework**: React 19.1.1 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4.1.16
- **Maps**: Leaflet 1.9.4 with react-leaflet
- **State Management**: TanStack Query (React Query) for server state
- **Routing**: React Router DOM 7.9.5
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Web Server**: Gunicorn (production)
- **Database**: PostgreSQL with health checks
- **CORS**: Configured for cross-origin requests

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10 or higher
- Node.js 18 or higher and npm
- PostgreSQL 15 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- Git

## Installation

### Option 1: Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/metincd/SWE573-FALL2025.git
cd SWE573-FALL2025
```

2. Create a `.env` file in the root directory:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/

### Option 2: Manual Installation

#### Backend Setup

1. Navigate to the project root directory:
```bash
cd SWE573-FALL2025
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file or export environment variables
export DEBUG=True
export SECRET_KEY=your-secret-key-here
export DB_NAME=hive_db
export DB_USER=hive_user
export DB_PASSWORD=hive_password
export DB_HOST=localhost
export DB_PORT=5432
```

5. Create PostgreSQL database:
```bash
createdb hive_db
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

8. Start the development server:
```bash
python manage.py runserver
```

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd hive_frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Project Structure

```
SWE573-FALL2025/
├── hive_backend/          # Django backend application
│   ├── settings.py        # Development settings
│   ├── settings_prod.py    # Production settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── the_hive/              # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # API viewsets
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # App URL routing
│   ├── admin.py           # Django admin configuration
│   └── migrations/        # Database migrations
├── hive_frontend/         # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts (Auth, etc.)
│   │   ├── api.ts         # API client configuration
│   │   └── main.tsx       # Application entry point
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
├── media/                 # User-uploaded files
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.backend     # Backend Docker image
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Usage

### Getting Started

1. **Registration**: Create an account with your email address and password. You'll automatically receive 3 TBH as a welcome bonus.

2. **Profile Setup**: Complete your profile by adding a display name, bio, avatar, and location. Your location helps other users find services nearby.

3. **Creating Services**: 
   - Click "Create Service" to post an offer or need
   - Add a title, description, estimated hours, and location
   - Tag your service with relevant semantic tags
   - Optionally upload an image

4. **Requesting Services**: 
   - Browse services on the map or list view
   - Click on a service to view details
   - Send a service request with an optional message
   - Wait for the service owner to accept or reject

5. **Completing Services**:
   - Once accepted, coordinate details through private messaging
   - After the service is performed, both parties confirm completion
   - Time credits are automatically transferred upon mutual confirmation

### Key Concepts

- **Time Bank Hours (TBH)**: Virtual currency where 1 hour of service = 1 TBH
- **Service Offers**: Services you're willing to provide to others
- **Service Needs**: Services you're seeking from others
- **Service Requests**: Requests sent to service owners
- **Conversations**: Private messaging channels created automatically when requests are accepted

## API Documentation

The REST API follows standard RESTful conventions. Main endpoints include:

- `/api/register/` - User registration
- `/api/token/` - JWT token authentication
- `/api/me/` - Current user profile
- `/api/services/` - Service management
- `/api/service-requests/` - Service request management
- `/api/conversations/` - Private messaging
- `/api/threads/` - Forum threads
- `/api/reviews/` - Review system
- `/api/time-accounts/` - Time banking
- `/api/reports/` - Content reporting
- `/api/admin/stats/` - Admin statistics

## Development

### Running Tests

```bash
# Backend tests
python manage.py test

# Frontend tests
cd hive_frontend
npm test
```

### Code Style

- Backend: Follow PEP 8 Python style guide
- Frontend: ESLint configuration included, follow React best practices
- TypeScript: Strict mode enabled

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Deployment

The application is currently deployed on AWS EC2 using Docker Compose. The production deployment includes:

- **Frontend**: Served on port 3000
- **Backend API**: Django REST Framework on port 8000
- **Database**: PostgreSQL container
- **Infrastructure**: AWS EC2 instance in eu-central-1 region

### Production Deployment Steps

1. Set environment variables for production:
```bash
export DEBUG=False
export SECRET_KEY=your-production-secret-key
export ALLOWED_HOSTS=your-domain.com,ec2-52-59-134-106.eu-central-1.compute.amazonaws.com
export CORS_ALLOWED_ORIGINS=http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:3000
```

2. Use production settings:
```bash
export DJANGO_SETTINGS_MODULE=hive_backend.settings_prod
```

3. Collect static files:
```bash
python manage.py collectstatic --noinput
```

4. Use production Docker Compose:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### AWS Deployment Notes

- Ensure security groups allow inbound traffic on ports 3000 (frontend) and 8000 (backend API)
- Configure environment variables securely using AWS Systems Manager Parameter Store or similar
- Set up regular database backups
- Monitor application logs and system resources

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write clear commit messages
- Follow existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## License

This project is developed for educational purposes as part of the SWE573 course at Boğaziçi University.

## Authors

- https://github.com/metincd

## Acknowledgments

- OpenStreetMap for geocoding services
- Leaflet for map visualization
- Django and React communities for excellent documentation
- Boğaziçi University SWE573 course instructors

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

## Version History

- **v1.0.0** (2025) - Initial release with core time banking features

---
