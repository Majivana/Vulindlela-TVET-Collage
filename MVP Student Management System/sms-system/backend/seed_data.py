"""
Seed Data Script

Populates the database with sample data for testing and development.

Usage:
    python seed_data.py

This creates:
- Sample users (students, lecturers, admin)
- Study modules for each sector
- Venues and timetable slots
- Campus map points
- Sample announcements
"""

import sys
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile, ApplicationStatus, StudySector
from app.models.lecturer import Lecturer, Department
from app.models.module import Module, ModuleLevel, ModuleStatus, StudySector as ModuleSector
from app.models.timetable import Venue, TimetableSlot, SlotType, DayOfWeek
from app.models.campus_map import CampusMapPoint, MapPointType
from app.models.announcement import Announcement, AnnouncementTarget, AnnouncementPriority


def create_users(db: Session):
    """Create sample users."""
    print("Creating users...")
    
    users = []
    
    # Admin user
    admin = User(
        email="admin@college.ac.za",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        first_name="Admin",
        last_name="User",
        phone="0211234567",
        is_active=True,
        email_verified=True,
    )
    db.add(admin)
    db.flush()
    users.append(admin)
    print(f"  Created admin: {admin.email}")
    
    # Lecturers for each department
    lecturers_data = [
        {"email": "lecturer.diesel@college.ac.za", "first_name": "John", "last_name": "Smith", "dept": Department.DIESEL_MECHANICS},
        {"email": "lecturer.plumbing@college.ac.za", "first_name": "Sarah", "last_name": "Johnson", "dept": Department.PLUMBING},
        {"email": "lecturer.electrical@college.ac.za", "first_name": "Michael", "last_name": "Brown", "dept": Department.ELECTRICAL},
        {"email": "lecturer.welding@college.ac.za", "first_name": "David", "last_name": "Wilson", "dept": Department.WELDING},
        {"email": "lecturer.ict@college.ac.za", "first_name": "Emily", "last_name": "Davis", "dept": Department.ICT},
    ]
    
    for i, data in enumerate(lecturers_data):
        user = User(
            email=data["email"],
            password_hash=get_password_hash("lecturer123"),
            role=UserRole.LECTURER,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=f"021123456{8+i}",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        
        lecturer = Lecturer(
            user_id=user.id,
            employee_number=f"EMP{1000+i}",
            department=data["dept"],
            qualification="Bachelor's Degree + Trade Certificate",
            years_of_experience=5 + i,
            is_full_time=True,
            is_active=True,
        )
        db.add(lecturer)
        users.append(user)
        print(f"  Created lecturer: {user.email} ({data['dept'].value})")
    
    # Sample students
    students_data = [
        {"email": "student1@student.college.ac.za", "first_name": "Thabo", "last_name": "Mokoena", "sector": StudySector.DIESEL_MECHANIC},
        {"email": "student2@student.college.ac.za", "first_name": "Lerato", "last_name": "Dlamini", "sector": StudySector.PLUMBING},
        {"email": "student3@student.college.ac.za", "first_name": "Sipho", "last_name": "Ndlovu", "sector": StudySector.ELECTRICIAN},
        {"email": "student4@student.college.ac.za", "first_name": "Nomsa", "last_name": "Khumalo", "sector": StudySector.WELDING},
        {"email": "student5@student.college.ac.za", "first_name": "Bongani", "last_name": "Zulu", "sector": StudySector.ICT},
    ]
    
    for i, data in enumerate(students_data):
        user = User(
            email=data["email"],
            password_hash=get_password_hash("student123"),
            role=UserRole.STUDENT,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=f"082123456{7+i}",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        
        student = StudentProfile(
            user_id=user.id,
            id_number=f"{9001015000000+i}",
            date_of_birth=date(2000, 1, 1),
            address=f"{123+i} Main Street",
            city="Cape Town",
            postal_code="8001",
            emergency_contact_name="Parent/Guardian",
            emergency_contact_phone="0829876543",
            sector=data["sector"],
            application_status=ApplicationStatus.ENROLLED,
            application_date=datetime.utcnow() - timedelta(days=30),
            enrollment_date=date.today() - timedelta(days=7),
            student_number=f"STU2024{1000+i}",
            funded=True,
            funding_amount=35000.00,
            funding_source="NSFAS",
            funding_reference=f"NSFAS{10000+i}",
        )
        db.add(student)
        users.append(user)
        print(f"  Created student: {user.email} ({data['sector'].value})")
    
    db.commit()
    return users


def create_modules(db: Session):
    """Create sample modules for each sector."""
    print("\nCreating modules...")
    
    # Get lecturers
    lecturers = db.query(Lecturer).all()
    lecturer_map = {l.department: l for l in lecturers}
    
    modules_data = [
        # Diesel Mechanic
        {"code": "DM101", "title": "Introduction to Diesel Engines", "sector": ModuleSector.DIESEL_MECHANIC, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.DIESEL_MECHANICS},
        {"code": "DM102", "title": "Fuel Systems", "sector": ModuleSector.DIESEL_MECHANIC, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.DIESEL_MECHANICS},
        {"code": "DM201", "title": "Advanced Engine Diagnostics", "sector": ModuleSector.DIESEL_MECHANIC, "level": ModuleLevel.LEVEL_2, "credits": 25, "lecturer_dept": Department.DIESEL_MECHANICS},
        
        # Plumbing
        {"code": "PL101", "title": "Plumbing Fundamentals", "sector": ModuleSector.PLUMBING, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.PLUMBING},
        {"code": "PL102", "title": "Water Supply Systems", "sector": ModuleSector.PLUMBING, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.PLUMBING},
        {"code": "PL201", "title": "Drainage and Sanitation", "sector": ModuleSector.PLUMBING, "level": ModuleLevel.LEVEL_2, "credits": 25, "lecturer_dept": Department.PLUMBING},
        
        # Electrical
        {"code": "EL101", "title": "Electrical Principles", "sector": ModuleSector.ELECTRICIAN, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.ELECTRICAL},
        {"code": "EL102", "title": "Wiring and Installation", "sector": ModuleSector.ELECTRICIAN, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.ELECTRICAL},
        {"code": "EL201", "title": "Industrial Electrical Systems", "sector": ModuleSector.ELECTRICIAN, "level": ModuleLevel.LEVEL_2, "credits": 25, "lecturer_dept": Department.ELECTRICAL},
        
        # Welding
        {"code": "WL101", "title": "Welding Safety and Basics", "sector": ModuleSector.WELDING, "level": ModuleLevel.LEVEL_1, "credits": 15, "lecturer_dept": Department.WELDING},
        {"code": "WL102", "title": "Arc Welding Techniques", "sector": ModuleSector.WELDING, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.WELDING},
        {"code": "WL201", "title": "Advanced Metal Fabrication", "sector": ModuleSector.WELDING, "level": ModuleLevel.LEVEL_2, "credits": 25, "lecturer_dept": Department.WELDING},
        
        # ICT
        {"code": "ICT101", "title": "Computer Fundamentals", "sector": ModuleSector.ICT, "level": ModuleLevel.LEVEL_1, "credits": 15, "lecturer_dept": Department.ICT},
        {"code": "ICT102", "title": "Networking Basics", "sector": ModuleSector.ICT, "level": ModuleLevel.LEVEL_1, "credits": 20, "lecturer_dept": Department.ICT},
        {"code": "ICT201", "title": "Programming and Web Development", "sector": ModuleSector.ICT, "level": ModuleLevel.LEVEL_2, "credits": 25, "lecturer_dept": Department.ICT},
    ]
    
    modules = []
    for data in modules_data:
        lecturer = lecturer_map.get(data["lecturer_dept"])
        module = Module(
            code=data["code"],
            title=data["title"],
            sector=data["sector"],
            level=data["level"],
            credits=data["credits"],
            description=f"This module covers fundamental concepts and practical skills in {data['title']}.",
            theory_hours=data["credits"] * 2,
            practical_hours=data["credits"] * 3,
            status=ModuleStatus.ACTIVE,
            lecturer_id=lecturer.id if lecturer else None,
        )
        db.add(module)
        modules.append(module)
        print(f"  Created module: {module.code} - {module.title}")
    
    db.commit()
    return modules


def create_venues(db: Session):
    """Create sample venues."""
    print("\nCreating venues...")
    
    venues_data = [
        {"name": "Main Lecture Hall A", "code": "LHA", "building": "Main Building", "floor": 1, "room_number": "101", "capacity": 100, "lat": -33.9249, "lng": 18.4241},
        {"name": "Main Lecture Hall B", "code": "LHB", "building": "Main Building", "floor": 1, "room_number": "102", "capacity": 80, "lat": -33.9250, "lng": 18.4242},
        {"name": "Diesel Workshop", "code": "DW", "building": "Workshop Block", "floor": 0, "room_number": "W01", "capacity": 30, "lat": -33.9252, "lng": 18.4240},
        {"name": "Plumbing Workshop", "code": "PW", "building": "Workshop Block", "floor": 0, "room_number": "W02", "capacity": 25, "lat": -33.9253, "lng": 18.4241},
        {"name": "Electrical Lab", "code": "EL", "building": "Technical Block", "floor": 1, "room_number": "201", "capacity": 40, "lat": -33.9248, "lng": 18.4243},
        {"name": "Welding Workshop", "code": "WW", "building": "Workshop Block", "floor": 0, "room_number": "W03", "capacity": 20, "lat": -33.9254, "lng": 18.4239},
        {"name": "Computer Lab 1", "code": "CL1", "building": "ICT Block", "floor": 2, "room_number": "301", "capacity": 35, "lat": -33.9247, "lng": 18.4244},
        {"name": "Computer Lab 2", "code": "CL2", "building": "ICT Block", "floor": 2, "room_number": "302", "capacity": 35, "lat": -33.9246, "lng": 18.4245},
    ]
    
    venues = []
    for data in venues_data:
        venue = Venue(
            name=data["name"],
            code=data["code"],
            building=data["building"],
            floor=data["floor"],
            room_number=data["room_number"],
            venue_type="classroom" if "Lecture" in data["name"] or "Lab" in data["name"] else "workshop",
            capacity=data["capacity"],
            lat=data["lat"],
            lng=data["lng"],
            is_active=True,
        )
        db.add(venue)
        venues.append(venue)
        print(f"  Created venue: {venue.name}")
    
    db.commit()
    return venues


def create_campus_map_points(db: Session):
    """Create campus map points."""
    print("\nCreating campus map points...")
    
    points_data = [
        {"name": "Main Entrance", "type": MapPointType.ENTRANCE, "building": "Main Building", "lat": -33.9245, "lng": 18.4240},
        {"name": "Reception", "type": MapPointType.RECEPTION, "building": "Main Building", "floor": 0, "room_number": "001", "lat": -33.9246, "lng": 18.4241},
        {"name": "Administration Office", "type": MapPointType.ADMIN_OFFICE, "building": "Main Building", "floor": 1, "room_number": "110", "lat": -33.9247, "lng": 18.4242},
        {"name": "Student Cafeteria", "type": MapPointType.CAFETERIA, "building": "Student Center", "floor": 0, "lat": -33.9250, "lng": 18.4245},
        {"name": "Library", "type": MapPointType.LIBRARY, "building": "Learning Center", "floor": 1, "lat": -33.9248, "lng": 18.4246},
        {"name": "Main Parking", "type": MapPointType.PARKING, "building": "Parking Area A", "lat": -33.9240, "lng": 18.4235},
        {"name": "Security Office", "type": MapPointType.SECURITY, "building": "Main Gate", "lat": -33.9244, "lng": 18.4239},
        {"name": "First Aid Station", "type": MapPointType.FIRST_AID, "building": "Main Building", "floor": 0, "room_number": "005", "lat": -33.9249, "lng": 18.4243},
    ]
    
    for data in points_data:
        point = CampusMapPoint(
            name=data["name"],
            point_type=data["type"],
            building=data["building"],
            floor=data.get("floor"),
            room_number=data.get("room_number"),
            lat=data["lat"],
            lng=data["lng"],
            is_active=True,
        )
        db.add(point)
        print(f"  Created map point: {point.name}")
    
    db.commit()


def create_announcements(db: Session):
    """Create sample announcements."""
    print("\nCreating announcements...")
    
    # Get admin user
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    
    announcements_data = [
        {
            "title": "Welcome to the New Academic Year",
            "body": "We are excited to welcome all students to the 2024 academic year. Please check your timetables and ensure you are enrolled in all required modules.",
            "target": AnnouncementTarget.GLOBAL,
            "priority": AnnouncementPriority.HIGH,
            "is_pinned": True,
        },
        {
            "title": "Campus WiFi Upgrade",
            "body": "We have upgraded our campus WiFi infrastructure. Please use the network 'College-Student' with your student number as the username.",
            "target": AnnouncementTarget.STUDENTS,
            "priority": AnnouncementPriority.NORMAL,
        },
        {
            "title": "Assignment Submission Guidelines",
            "body": "All assignments must be submitted through the online portal. Late submissions will incur a 10% penalty per day unless prior arrangements have been made.",
            "target": AnnouncementTarget.STUDENTS,
            "priority": AnnouncementPriority.NORMAL,
        },
        {
            "title": "Staff Meeting - March 2024",
            "body": "All lecturers and staff are required to attend the quarterly staff meeting on March 15th at 10:00 AM in the Main Lecture Hall.",
            "target": AnnouncementTarget.LECTURERS,
            "priority": AnnouncementPriority.HIGH,
        },
    ]
    
    for data in announcements_data:
        announcement = Announcement(
            author_id=admin.id if admin else 1,
            title=data["title"],
            body=data["body"],
            target=data["target"],
            priority=data["priority"],
            is_pinned=data.get("is_pinned", False),
            is_published=True,
        )
        db.add(announcement)
        print(f"  Created announcement: {announcement.title}")
    
    db.commit()


def main():
    """Main function to seed the database."""
    print("=" * 60)
    print("Student Management System - Database Seeding")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create tables
        init_db()
        
        # Seed data
        create_users(db)
        create_modules(db)
        create_venues(db)
        create_campus_map_points(db)
        create_announcements(db)
        
        print("\n" + "=" * 60)
        print("Database seeded successfully!")
        print("=" * 60)
        print("\nDefault login credentials:")
        print("  Admin: admin@college.ac.za / admin123")
        print("  Lecturer: lecturer.diesel@college.ac.za / lecturer123")
        print("  Student: student1@student.college.ac.za / student123")
        
    except Exception as e:
        print(f"\nError seeding database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
