# Student Management System (SMS)

A comprehensive Student Management System for Technical Vocational Colleges offering programs in Diesel Mechanics, Plumbing, Electrical, Welding, and ICT.

![SMS Dashboard](docs/images/dashboard-preview.png)

## Features

### For Students
- **Online Application & Registration** - Apply for admission and track application status
- **Student Dashboard** - Overview of modules, attendance, assignments, and announcements
- **Attendance Tracking** - GPS-based check-in/check-out with geofence validation
- **Module Management** - View enrolled modules, timetables, and course materials
- **Assignment Submission** - Submit assignments online with file uploads
- **Results Viewing** - View grades and academic progress
- **Helpdesk Support** - Create and track support tickets
- **Campus Navigation** - Interactive map with points of interest
- **Funding Status** - Track funding applications and disbursements

### For Lecturers
- **Assignment Management** - Create assignments and grade submissions
- **Attendance Monitoring** - View student attendance records
- **Hours Approval** - Approve practical/workshop hours logged by students
- **Announcement Publishing** - Post announcements for students
- **Results Management** - Record and publish student grades

### For Administrators
- **User Management** - Manage students, lecturers, and staff accounts
- **Course Management** - Create and manage modules and programs
- **Timetable Management** - Schedule classes and manage venues
- **Application Processing** - Review and process student applications
- **Supplier Management** - Manage vendor and supplier information
- **System Configuration** - Configure campus boundaries and settings

## Technology Stack

### Backend
- **Python 3.11+** with FastAPI
- **SQLAlchemy 2.0** ORM
- **PostgreSQL** database
- **JWT** authentication with refresh tokens
- **Pydantic** for data validation
- **Argon2** for password hashing

### Frontend
- **HTML5** with Bootstrap 5
- **JavaScript** (vanilla)
- **Font Awesome** icons
- **Leaflet.js** for maps

### Infrastructure
- **Docker** & Docker Compose
- **Nginx** (optional, for production)

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (optional)

### Installation

1. Clone or download the repository:
```bash
cd sms-system
```

2. Start the services:
```bash
docker-compose up -d
```

3. Wait for the database to initialize (about 30 seconds)

4. Access the application:
   - Frontend: http://localhost:8000 (or open `frontend/templates/index.html`)
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

5. Create your first admin user (optional):
```bash
# Access the backend container
docker-compose exec backend python -c "
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email='admin@college.ac.za',
    password_hash=get_password_hash('admin123'),
    role=UserRole.ADMIN,
    first_name='Admin',
    last_name='User',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created successfully')
"
```

### Development Setup (without Docker)

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
sms-system/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   ├── core/              # Core configuration & security
│   │   ├── db/                # Database configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── main.py            # Application entry point
│   ├── uploads/               # File upload directory
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # HTML/CSS/JS frontend
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS, images
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/me` - Get current user info

### Students
- `GET /api/students/profile` - Get student profile
- `PUT /api/students/profile` - Update profile
- `POST /api/students/application/submit` - Submit application
- `GET /api/students/application/status` - Check application status
- `POST /api/students/documents/upload` - Upload documents

### Attendance
- `GET /api/attendance/geofence/status` - Check geofence status
- `POST /api/attendance/checkin` - Check in
- `POST /api/attendance/checkout` - Check out
- `GET /api/attendance/history` - Get attendance history
- `GET /api/attendance/summary` - Get attendance summary

### Modules
- `GET /api/modules/` - List all modules
- `GET /api/modules/{id}` - Get module details
- `POST /api/modules/{id}/enroll` - Enroll in module
- `GET /api/modules/my/enrolled` - Get enrolled modules

### Assignments
- `GET /api/assignments/my` - Get my assignments
- `GET /api/assignments/{id}` - Get assignment details
- `POST /api/assignments/{id}/submit` - Submit assignment
- `GET /api/assignments/{id}/submission` - Get my submission

### Tickets (Helpdesk)
- `GET /api/tickets/my` - Get my tickets
- `POST /api/tickets/` - Create ticket
- `GET /api/tickets/{id}` - Get ticket details
- `POST /api/tickets/{id}/reply` - Add reply

### Dashboard
- `GET /api/dashboard/student` - Student dashboard data
- `GET /api/dashboard/lecturer` - Lecturer dashboard data
- `GET /api/dashboard/admin` - Admin dashboard data

## Configuration

### Environment Variables

Create a `.env` file in the backend directory with:

```env
# Application
APP_NAME="Student Management System"
DEBUG=false
SECRET_KEY=your-super-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sms_db

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Campus Geofence
CAMPUS_LAT=-33.9249
CAMPUS_LNG=18.4241
CAMPUS_RADIUS=500

# File Uploads
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx,jpg,jpeg,png
```

## User Roles

- **Student** - Access to personal dashboard, modules, attendance, assignments
- **Lecturer** - Create assignments, grade submissions, approve hours
- **Admin** - Full system access, user management, course management
- **Support Agent** - Handle helpdesk tickets
- **Supplier Manager** - Manage supplier information

## Database Schema

The system includes the following main entities:

- **User** - Authentication and basic profile
- **StudentProfile** - Extended student information
- **Lecturer** - Lecturer profile and assignments
- **Module** - Course modules and details
- **ModuleEnrollment** - Student-module relationships
- **TimetableSlot** - Class schedules
- **AttendanceRecord** - Attendance tracking with geolocation
- **Assignment** - Assignment definitions
- **Submission** - Student submissions
- **Announcement** - System announcements
- **Ticket** - Helpdesk tickets
- **Supplier** - Vendor management
- **CampusMapPoint** - Points of interest for navigation

## Security Features

- JWT-based authentication with refresh tokens
- Password hashing with Argon2
- Role-based access control (RBAC)
- Geofence validation for attendance
- File upload validation and size limits
- CORS protection
- Input validation with Pydantic

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Geolocation features require HTTPS in production.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, email support@college.ac.za or create a ticket through the helpdesk system.

## Roadmap

- [ ] Mobile app (React Native/Flutter)
- [ ] Google Calendar integration
- [ ] Push notifications
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] SMS notifications

---

Built with ❤️ for Technical Vocational Education
