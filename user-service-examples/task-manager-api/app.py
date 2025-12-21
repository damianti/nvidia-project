#!/usr/bin/env python3
"""
Task Manager API - Production-ready service example
A complete REST API with authentication, database, and CRUD operations.
"""
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400)))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

PORT = int(os.getenv("PORT", "8080"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "task-manager-api")
VERSION = "1.0.0"

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, high
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }

# Initialize database
with app.app_context():
    os.makedirs('data', exist_ok=True)
    db.create_all()

# Helper Functions
def validate_priority(priority):
    """Validate priority value"""
    return priority in ['low', 'medium', 'high']

# Routes

@app.route("/", methods=["GET"])
def root():
    """Root endpoint - API information"""
    return jsonify({
        "service": SERVICE_NAME,
        "version": VERSION,
        "status": "running",
        "port": PORT,
        "message": "Welcome to Task Manager API",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "me": "GET /auth/me (requires JWT)"
            },
            "tasks": {
                "list": "GET /tasks (requires JWT)",
                "create": "POST /tasks (requires JWT)",
                "get": "GET /tasks/<id> (requires JWT)",
                "update": "PUT /tasks/<id> (requires JWT)",
                "delete": "DELETE /tasks/<id> (requires JWT)"
            },
            "health": "GET /health"
        },
        "documentation": "/docs (Swagger UI)"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": SERVICE_NAME,
        "database": "connected" if db.engine else "disconnected"
    }), 200

# Authentication Routes

@app.route("/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        
        if not email or "@" not in email:
            return jsonify({"error": "Valid email is required"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict(),
            "access_token": access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    """Login user and get JWT token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route("/auth/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

# Task Routes

@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    """Get all tasks for current user with optional filtering"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        completed = request.args.get('completed', type=str)
        priority = request.args.get('priority', type=str)
        search = request.args.get('search', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Base query
        query = Task.query.filter_by(user_id=user_id)
        
        # Apply filters
        if completed is not None:
            query = query.filter_by(completed=completed.lower() == 'true')
        
        if priority and validate_priority(priority):
            query = query.filter_by(priority=priority)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Task.title.like(search_term),
                    Task.description.like(search_term)
                )
            )
        
        # Pagination
        pagination = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "tasks": [task.to_dict() for task in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get tasks: {str(e)}"}), 500

@app.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    """Create a new task"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        priority = data.get("priority", "medium").lower()
        due_date_str = data.get("due_date")
        
        # Validation
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        if not validate_priority(priority):
            return jsonify({"error": "Priority must be 'low', 'medium', or 'high'"}), 400
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Invalid due_date format. Use ISO 8601 format"}), 400
        
        # Create task
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            user_id=user_id
        )
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            "message": "Task created successfully",
            "task": task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create task: {str(e)}"}), 500

@app.route("/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    """Get a specific task"""
    try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        return jsonify({
            "task": task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get task: {str(e)}"}), 500

@app.route("/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    """Update a task"""
    try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields
        if "title" in data:
            title = data["title"].strip()
            if title:
                task.title = title
        
        if "description" in data:
            task.description = data["description"].strip()
        
        if "completed" in data:
            task.completed = bool(data["completed"])
        
        if "priority" in data:
            priority = data["priority"].lower()
            if validate_priority(priority):
                task.priority = priority
            else:
                return jsonify({"error": "Priority must be 'low', 'medium', or 'high'"}), 400
        
        if "due_date" in data:
            due_date_str = data["due_date"]
            if due_date_str:
                try:
                    task.due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({"error": "Invalid due_date format"}), 400
            else:
                task.due_date = None
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Task updated successfully",
            "task": task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    try:
        user_id = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            "message": "Task deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME} v{VERSION} on port {PORT}...")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
