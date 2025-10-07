from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    usn = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    section = Column(String)
    password = Column(String)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    subject = Column(String)
    email = Column(String)
    availability = Column(Text)  # JSON string for daily availability

class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String)
    semester = Column(Integer)
    subject = Column(String)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    teacher_specialization = Column(String)  # new column
    day = Column(String)
    time = Column(String)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_type = Column(String)  # student/admin
    user_id = Column(Integer)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
