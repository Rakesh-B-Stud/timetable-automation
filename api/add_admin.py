from database import SessionLocal
from models import Admin

# Create database session
db = SessionLocal()

# Create a new admin account
new_admin = Admin(username="admin", password="admin123")

# Add and commit
db.add(new_admin)
db.commit()

print("✅ Admin added successfully! Username: admin | Password: admin123")

# Close the session
db.close()
