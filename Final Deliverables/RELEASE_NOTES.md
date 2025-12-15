## Release Notes

### Final Deliverables Release

This pre-release version has been prepared for the SWE573 Software Development Practice course final submission.

###  Features

- Fully functional time banking system
- Service exchange platform
- User management and authentication
- Map-based service visualization
- Messaging and forum system
- Moderation and admin panel

### Deployment

**Live Application**: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:3000/

**Backend API**: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000/api

**Admin Panel**: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000/admin

###  Technology Stack

- **Backend**: Django 4.2.25 + Django REST Framework 3.16.1
- **Frontend**: React 19.1.1 + TypeScript + Vite
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker + AWS EC2
- **Maps**: Leaflet with react-leaflet
- **Authentication**: JWT (JSON Web Tokens)

###  Links

- **Repository**: https://github.com/metincd/SWE573-FALL2025
- **Frontend**: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:3000/
- **Backend API**: http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000/api

###  Key Features

#### Service Exchange
- Create service offers and needs
- Interactive map visualization with Leaflet
- Service requests and management
- Two-party confirmation system
- Automatic time credit transfers

#### Time Banking System
- Virtual currency: Time Bank Hours (TBH)
- Initial balance: 3 TBH for new users
- Transaction history and audit trail
- Automatic balance updates

#### User Management
- User registration and JWT authentication
- User profiles with avatars
- Location-based services
- User ratings and reviews

#### Communication Features
- Private messaging system
- Public forum discussions
- Service-specific discussion threads
- Thank you notes

#### Moderation & Administration
- Content reporting system
- Admin panel with statistics
- User ban/suspension capabilities
- Content moderation tools

###  Important Notes

- This is a **pre-release** version for course deliverables
- The application is deployed on AWS EC2
- HTTP only (no SSL/TLS certificate)
- Single instance deployment

###  Course Information

**Course**: SWE573 Software Development Practice  
**University**: Boğaziçi University  
**Semester**: Fall 2025
