from fastapi import FastAPI, UploadFile, File, Request, Depends, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pandas as pd
from database import Base, engine, get_db
from models import Student, Teacher, Timetable, Notification, Admin
from utils import generate_timetable

# -----------------------
# Initialize app & templates
# -----------------------
app = FastAPI()
templates = Jinja2Templates(directory="frontend")

# -----------------------
# FRONTEND ROUTES
# -----------------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/student", response_class=HTMLResponse)
def student_page(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

# Redirect for .html requests
@app.get("/admin.html")
def admin_html_redirect():
    return RedirectResponse("/admin")

@app.get("/student.html")
def student_html_redirect():
    return RedirectResponse("/student")

# -----------------------
# LOGIN ENDPOINTS
# -----------------------
@app.post("/login/student")
def login_student(data: dict = Body(...), db: Session = Depends(get_db)):
    usn = data.get("usn")
    password = data.get("password")
    student = db.query(Student).filter(Student.usn == usn, Student.password == password).first()
    if student:
        return {
            "message": "Student login successful",
            "role": "student",
            "id": student.id,
            "name": student.name,
            "usn": student.usn,
            "section": student.section
        }
    return JSONResponse(status_code=401, content={"error": "Invalid USN or password"})

@app.post("/login/admin")
def login_admin(data: dict = Body(...), db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")
    admin = db.query(Admin).filter(Admin.username == username, Admin.password == password).first()
    if admin:
        return {"message": "Admin login successful", "role": "admin", "username": admin.username}
    return JSONResponse(status_code=401, content={"error": "Invalid username or password"})

# -----------------------
# UPLOAD STUDENTS
# -----------------------
@app.post("/upload/students")
async def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.StringIO(contents.decode("utf-8")))
        uploaded, skipped = 0, 0
        for _, row in df.iterrows():
            usn = str(row.get("usn", "")).strip()
            email = str(row.get("email", "")).strip()
            name = str(row.get("name", "")).strip()
            section = str(row.get("section", "")).strip()
            if not usn or not email:
                skipped += 1
                continue
            if db.query(Student).filter((Student.usn == usn) | (Student.email == email)).first():
                skipped += 1
                continue
            student = Student(usn=usn, name=name, email=email, section=section, password="default123")
            db.add(student)
            uploaded += 1
        db.commit()
        return JSONResponse(content={"message": f"Students uploaded: {uploaded} added, {skipped} skipped."})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})

# -----------------------
# UPLOAD TEACHERS
# -----------------------
@app.post("/upload/teachers")
async def upload_teachers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.StringIO(contents.decode("utf-8")))
        uploaded, skipped = 0, 0
        for _, row in df.iterrows():
            email = str(row.get("email", "")).strip()
            name = str(row.get("name", "")).strip()
            subject = str(row.get("subject", "")).strip()
            specialization = str(row.get("specialization", "")).strip()
            availability = str(row.get("availability", "available")).strip()
            profile_pic = str(row.get("profile_pic", "")).strip()
            if not email:
                skipped += 1
                continue
            if db.query(Teacher).filter(Teacher.email == email).first():
                skipped += 1
                continue
            teacher = Teacher(
                name=name, subject=subject, specialization=specialization,
                email=email, availability=availability, profile_pic=profile_pic
            )
            db.add(teacher)
            uploaded += 1
        db.commit()
        return JSONResponse(content={"message": f"Teachers uploaded: {uploaded} added, {skipped} skipped."})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})

# -----------------------
# GENERATE TIMETABLE
# -----------------------
@app.post("/generate/timetable")
def generate_timetable_endpoint(section: str = Body(...), semester: int = Body(...), db: Session = Depends(get_db)):
    teachers = db.query(Teacher).all()
    days = ["Mon","Tue","Wed","Thu","Fri"]
    times = ["9-10","10-11","11-12","12-1","2-3"]

    timetable = generate_timetable(section, semester, [t.subject for t in teachers], days, times, db)

    enriched = []
    for entry in timetable:
        teacher = db.query(Teacher).filter(Teacher.id == entry['teacher_id']).first()
        enriched.append({
            "day": entry['day'],
            "time": entry['time'],
            "subject": entry['subject'],
            "teacher": {
                "name": teacher.name if teacher else "N/A",
                "availability": teacher.availability if teacher else "unavailable"
            }
        })
    return {"timetable": enriched}

# -----------------------
# FETCH TIMETABLE FOR STUDENTS
# -----------------------
@app.get("/timetable/{section}")
def get_timetable(section: str, db: Session = Depends(get_db)):
    timetable = db.query(Timetable).filter(Timetable.section == section).all()
    result = []
    for t in timetable:
        teacher = db.query(Teacher).filter(Teacher.id == t.teacher_id).first()
        student_usns = [s.usn for s in db.query(Student).filter(Student.section == section).all()]
        result.append({
            "day": t.day,
            "time": t.time,
            "subject": t.subject,
            "teacher": {
                "name": teacher.name if teacher else "N/A",
                "specialization": teacher.specialization if teacher else "N/A",
                "email": teacher.email if teacher else "N/A"
            },
            "students": student_usns
        })
    return JSONResponse(content=result)

# -----------------------
# FETCH NOTIFICATIONS
# -----------------------
@app.get("/notifications/{student_id}")
def get_notifications(student_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == student_id).all()
    return JSONResponse(content=[{"message": n.message, "timestamp": n.timestamp} for n in notifications])

# -----------------------
# ADMIN TEACHERS ENDPOINTS
# -----------------------
@app.get("/teachers")
def get_teachers(db: Session = Depends(get_db)):
    return [
        {
            "id": t.id,
            "name": t.name,
            "subject": t.subject,
            "specialization": t.specialization,
            "availability": t.availability,
            "profile_pic": t.profile_pic
        } for t in db.query(Teacher).all()
    ]

@app.post("/teacher/{teacher_id}/toggle")
def toggle_teacher_availability(teacher_id:int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id==teacher_id).first()
    if not teacher:
        return {"error":"Teacher not found"}
    teacher.availability = "available" if teacher.availability=="unavailable" else "unavailable"
    db.commit()
    return {"availability": teacher.availability}

# -----------------------
# PUBLISH TIMETABLE (placeholder)
# -----------------------
@app.post("/publish/timetable")
def publish_timetable(db: Session = Depends(get_db)):
    return {"message": "Timetable publishing not implemented yet."}
