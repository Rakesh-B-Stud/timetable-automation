import json
from sqlalchemy.orm import Session
from models import Teacher, Timetable, Notification, Student
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

# Replace with your SMTP details
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

async def send_email(to_email, subject, content):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(content)
    await aiosmtplib.send(message, hostname=SMTP_HOST, port=SMTP_PORT,
                          username=SMTP_USER, password=SMTP_PASS, start_tls=True)

def select_teacher(subject, available_teachers):
    # 1. Check teacher with same subject available
    for t in available_teachers:
        t_avail = json.loads(t.availability or "{}")
        if subject.lower() in t.subject.lower() and t_avail.get('available', True):
            return t
    # 2. Any free teacher
    for t in available_teachers:
        t_avail = json.loads(t.availability or "{}")
        if t_avail.get('available', True):
            return t
    return None  # No teacher available

def generate_timetable(section, semester, subjects, days, times, db: Session):
    teachers = db.query(Teacher).all()
    students = db.query(Student).filter(Student.section == section).all()

    for day in days:
        for time, subject in zip(times, subjects):
            teacher = select_teacher(subject, teachers)
            if teacher:
                timetable_entry = Timetable(
                    section=section,
                    semester=semester,
                    subject=subject,
                    teacher_id=teacher.id,
                    day=day,
                    time=time
                )
                db.add(timetable_entry)
            else:
                # Notify students if class terminated
                msg = f"Class {subject} for section {section} at {time} on {day} is terminated due to no teacher available."
                for s in students:
                    notification = Notification(
                        user_type="student",
                        user_id=s.id,
                        message=msg
                    )
                    db.add(notification)
                    send_email(s.email, "Class Termination Alert", msg)
    db.commit()
    return {"message": f"Timetable generated for {section} semester {semester}"}
# utils.py
# utils.py
def send_timetable_pdf(email, timetable):
    # TODO: Implement actual PDF generation and email sending
    print(f"Sending timetable to {email}")

