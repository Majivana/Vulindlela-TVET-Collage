# Quick Start Guide - Student Management System

## Prerequisites

- Docker and Docker Compose installed
- Web browser (Chrome, Firefox, Safari, or Edge)

## Running the Application

### Option 1: Using Docker (Recommended)

1. Navigate to the project directory:
```bash
cd sms-system
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to initialize (about 30 seconds)

4. Access the application:
   - **Public Website**: Open `frontend/templates/index.html` in your browser
   - **API Documentation**: http://localhost:8000/api/docs
   - **Health Check**: http://localhost:8000/health

5. Stop services:
```bash
docker-compose down
```

### Option 2: Local Development

#### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

The frontend consists of static HTML files. Simply open them in your browser:
- `frontend/templates/index.html` - Landing page
- `frontend/templates/login.html` - Login page
- `frontend/templates/dashboard.html` - Student dashboard

## Default Login Credentials

After running the seed data script, you can use these accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@college.ac.za | admin123 |
| Lecturer | lecturer.diesel@college.ac.za | lecturer123 |
| Student | student1@student.college.ac.za | student123 |

## Seeding Test Data

To populate the database with sample data:

```bash
# With Docker
docker-compose exec backend python seed_data.py

# Without Docker
cd backend
python seed_data.py
```

## Key Features

### For Students
1. **Apply Online** - Visit `index.html` and click "Apply Now"
2. **Track Application** - Login to see application status
3. **Check Attendance** - Use GPS-based check-in at `attendance.html`
4. **Submit Assignments** - Upload files through the assignments page
5. **Get Support** - Create helpdesk tickets

### For Lecturers
1. **Create Assignments** - Set due dates and requirements
2. **Grade Submissions** - Review and grade student work
3. **Approve Hours** - Verify practical/workshop hours

### For Admins
1. **Manage Users** - Create and manage accounts
2. **Process Applications** - Review student applications
3. **Configure System** - Set up modules, venues, and campus map

## API Endpoints

All API endpoints are prefixed with `/api`:

- `POST /api/auth/login` - Login
- `GET /api/dashboard/student` - Student dashboard data
- `GET /api/modules/` - List modules
- `POST /api/attendance/checkin` - Check in with GPS
- `GET /api/attendance/geofence/status` - Check geofence status

Full API documentation available at `/api/docs` when running the backend.

## Troubleshooting

### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### CORS Issues
Edit `backend/.env` and update:
```env
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,file://
```

## Next Steps

1. Customize the landing page (`frontend/templates/index.html`)
2. Update campus coordinates in `.env`
3. Add your institution's branding
4. Configure email notifications
5. Set up SSL/HTTPS for production

## Support

For issues or questions:
- Check the API documentation at `/api/docs`
- Review the README.md for detailed information
- Create a helpdesk ticket (when logged in)

---

**Note**: This is an MVP (Minimum Viable Product). Some features like Google Calendar integration are marked for future development.
