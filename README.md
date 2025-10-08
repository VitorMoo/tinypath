# UnaTrack

An intelligent academic activity management system with automated synchronization and email notifications.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/VitorMoo/unatrack)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.0-green.svg)](https://www.djangoproject.com/)

## Table of Contents

- [About](#about)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Commands](#commands)
- [License](#license)

## About

UnaTrack is a comprehensive academic activity management system designed to streamline deadline tracking and task management for university students. The platform integrates with the UNAERP academic portal to provide automated synchronization, intelligent notifications, and real-time progress tracking.

### Problem Statement

University students frequently face challenges with:
- Missing assignment deadlines
- Managing activities across multiple systems
- Lack of proactive deadline notifications
- Difficulty organizing courses and assignments

### Solution

UnaTrack addresses these challenges through:
- Automated synchronization with UNAERP academic portal
- Centralized dashboard for all academic activities
- Intelligent email alerts before assignment deadlines
- Task completion tracking
- Real-time statistics for overdue and upcoming activities

## Key Features

### 📊 Dashboard Completo
- [x] **Visão geral** com estatísticas de disciplinas e atividades
- [x] **Cards informativos** mostrando total de cursos, atividades e prazos próximos
- [x] **Lista de disciplinas** com contador de atividades por curso

### 📚 Gerenciamento de Disciplinas
- [x] **Visualização** de todas as disciplinas cadastradas
### Dashboard Management
- Comprehensive overview with course and assignment statistics
- Activity counters per course
- Real-time status tracking

### Course Management
- Course visualization with assignment counters
- Filter by specific courses
- Organized course listings

### Assignment Management
- Complete listing of all assignments
- Intelligent separation between assignments with and without deadlines
- Completion checkbox for task tracking
- Dynamic status badges:
  - Completed (when marked)
  - Overdue (past deadline and not completed)
  - Due Today
  - On Time
- Course-based filtering
- Real-time statistics:
  - Total assignments
  - Overdue assignments (excluding completed)
  - Upcoming assignments within 7 days (excluding completed)
  - Assignments without defined deadlines

### Automated Synchronization
- UNAERP portal scraping for courses and assignments
- Periodic synchronization via Celery (hourly)
- Securely encrypted credential storage
- Synchronization dashboard with status and history

### Notification System
- Email alerts for upcoming assignment deadlines
- Customizable configuration:
  - Alert advance notice (default: 3 days)
  - Enable/disable email notifications
- Responsive HTML email templates
- Automated daily delivery at 8:00 AM via Celery Beat
- Spam prevention - no duplicate alerts
- User preference compliance
- MailHog testing interface for development

### User Management
- Complete authentication system
- New user registration
- Secure login/logout sessions
- Account settings:
  - Update personal information
  - Change password
  - Configure notification preferences
  - Manage UNAERP credentials

### Quality Assurance
- Unit tests for critical functionalities
- Test coverage for:
  - Completion marking system
  - Email and notification delivery
  - Statistics and counters

## Technology Stack

### Backend
- **Python 3.12** - Programming language
- **Django 5.0** - Web framework
- **PostgreSQL 16** - Relational database
- **Celery 5.5** - Asynchronous processing and task scheduling
- **Redis** - Celery broker and caching
- **BeautifulSoup4** - UNAERP portal web scraping
- **Requests** - HTTP client for scraping

### Frontend
- **Bootstrap 5** - CSS framework
- **Bootstrap Icons** - Icon library
- **JavaScript (Vanilla)** - Interactivity (AJAX for checkboxes)

### DevOps & Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Container orchestration
- **MailHog** - SMTP server for development
- **Nginx** (planned) - Production web server

### Development Tools
- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Linting

## Installation

### Prerequisites

Ensure you have the following installed:
- [Docker](https://www.docker.com/get-started) (v20+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)
- [Git](https://git-scm.com/)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VitorMoo/unatrack.git
   cd unatrack
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit the .env file with your settings
   nano .env
   ```

   Important variables:
   ```env
   # Django
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=1

   # Database
   POSTGRES_DB=unatrack
   POSTGRES_USER=unatrack_user
   POSTGRES_PASSWORD=your-secure-password

   # Email (MailHog pre-configured)
   EMAIL_HOST=smtp
   EMAIL_PORT=1025
   DEFAULT_FROM_EMAIL=noreply@unatrack.com
   ```

3. **Start the containers:**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - Django Web Server (port 8000)
   - Celery Worker
   - Celery Beat
   - MailHog (ports 1025 SMTP and 8025 Web UI)

4. **Wait for initialization and access:**
   ```
   Application: http://localhost:8000
   MailHog (view emails): http://localhost:8025
   ```

5. **Create a superuser (optional):**
   ```bash
   docker exec -it unatrack_web python manage.py createsuperuser
   ```

6. **Access Django Admin (optional):**
   ```
   http://localhost:8000/admin
   ```

## Usage

### First Access

1. Navigate to http://localhost:8000
2. Click **"Register"**
3. Fill in your information and create your account
4. Login with your credentials

### UNAERP Synchronization Setup

1. In the top menu, click **"Settings"**
2. Scroll to the **"UNAERP Credentials"** section
3. Fill in:
   - UNAERP Username (RA)
   - Portal password
4. Click **"Save Credentials"**

### Synchronize Assignments

1. In the menu, click **"Synchronization"**
2. Click the **"Synchronize Now"** button
3. Wait for the process (may take a few seconds)
4. Your courses and assignments will appear on the dashboard

### Manage Assignments

1. Access **"Assignments"** in the menu
2. View all your organized assignments
3. **Mark as completed:** Click the checkbox next to the assignment
4. **Filter by course:** Use the filter at the top of the page
5. Track statistics:
   - Overdue
   - Upcoming (7 days)
   - No deadline

### Configure Email Alerts

1. Go to **"Settings"**
2. In the **"Notification Preferences"** section:
   - Check **"Receive email alerts"**
   - Set **"Days in advance"** (e.g., 3 days before)
3. Save the changes
4. You will receive daily emails at 8:00 AM with upcoming assignments

### View Emails (Development)

During development, emails are captured by MailHog:
- Access: http://localhost:8025
- View all sent emails
- Test templates and content

## Testing

### Run all tests
```bash
docker exec unatrack_web python manage.py test
```

### Run tests for a specific app
```bash
# User tests
docker exec unatrack_web python manage.py test user

# Notification tests
docker exec unatrack_web python manage.py test notifications
```

### With coverage
```bash
docker exec unatrack_web pytest --cov=. --cov-report=html
```

## Available Management Commands

### Send Email Alerts
```bash
# Send alerts to all eligible users
docker exec unatrack_web python manage.py send_assignment_alerts

# Dry run (test without sending emails)
docker exec unatrack_web python manage.py send_assignment_alerts --dry-run

# Send to specific user
docker exec unatrack_web python manage.py send_assignment_alerts --user-id=1
```

### Scraping Commands
```bash
# Trigger manual synchronization
docker exec unatrack_web python manage.py scrape_unaerp --user-id=1
```

### Database Commands
```bash
# Apply migrations
docker exec unatrack_web python manage.py migrate

# Create superuser
docker exec unatrack_web python manage.py createsuperuser

# Open Django shell
docker exec -it unatrack_web python manage.py shell
```

### Celery Management
```bash
# View registered tasks
docker exec unatrack_celery_beat celery -A config inspect registered

# View active workers
docker exec unatrack_celery_beat celery -A config inspect active

# View scheduled tasks (Beat)
docker exec unatrack_celery_beat celery -A config inspect scheduled
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Vitor Moreira**
- GitHub: [@VitorMoo](https://github.com/VitorMoo)
- LinkedIn: [Vitor Moreira](https://www.linkedin.com/in/vitor-moreira)

---

Developed as an academic project to solve real-world problems in assignment management and deadline tracking.
                ├── courses.html
                └── account_settings.html
```

---

Developed as an academic project to solve real-world problems in assignment management and deadline tracking.
