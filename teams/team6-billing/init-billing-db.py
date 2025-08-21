#!/usr/bin/env python3
"""
Initialize Billing Service Database
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.config import DATABASE_URL
from app.database.models import Base, User, Subscription, Billing

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def init_database():
    """Initialize the billing database with sample data"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("Database already has users. Skipping initialization.")
            return
        
        # Create sample users
        users_data = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "is_admin": True
            },
            {
                "username": "testuser1",
                "email": "user1@example.com",
                "password": "password123",
                "is_admin": False
            },
            {
                "username": "testuser2", 
                "email": "user2@example.com",
                "password": "password123",
                "is_admin": False
            }
        ]
        
        created_users = []
        for user_data in users_data:
            hashed_password = get_password_hash(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                is_admin=user_data["is_admin"]
            )
            db.add(user)
            created_users.append(user)
        
        db.commit()
        
        # Refresh users to get their IDs
        for user in created_users:
            db.refresh(user)
        
        # Create sample subscriptions
        subscriptions_data = [
            {
                "user_id": created_users[1].id,  # testuser1
                "plan_name": "Basic Plan",
                "plan_type": "basic",
                "max_containers": 5,
                "max_cpu": 1.0,
                "max_memory": "1g",
                "price_per_month": 10.0
            },
            {
                "user_id": created_users[2].id,  # testuser2
                "plan_name": "Pro Plan", 
                "plan_type": "pro",
                "max_containers": 20,
                "max_cpu": 4.0,
                "max_memory": "8g",
                "price_per_month": 50.0
            }
        ]
        
        for sub_data in subscriptions_data:
            subscription = Subscription(**sub_data)
            db.add(subscription)
        
        # Create sample billing records
        billing_data = [
            {
                "user_id": created_users[1].id,
                "amount": 10.0,
                "currency": "USD",
                "description": "Basic Plan - Monthly Subscription",
                "status": "paid"
            },
            {
                "user_id": created_users[2].id,
                "amount": 50.0,
                "currency": "USD", 
                "description": "Pro Plan - Monthly Subscription",
                "status": "paid"
            }
        ]
        
        for billing_data_item in billing_data:
            billing = Billing(**billing_data_item)
            db.add(billing)
        
        db.commit()
        
        print("✅ Billing database initialized successfully!")
        print(f"Created {len(created_users)} users:")
        for user in created_users:
            print(f"  - {user.username} ({user.email}) - Admin: {user.is_admin}")
        print(f"Created {len(subscriptions_data)} subscriptions")
        print(f"Created {len(billing_data)} billing records")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing Billing Service Database...")
    init_database()
    print("✅ Done!")




