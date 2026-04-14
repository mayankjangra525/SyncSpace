from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ------------------ USER ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    # 🔥 Relationships
    projects = db.relationship('Project', backref='owner', lazy=True)
    drive_files = db.relationship('DriveFile', backref='user', lazy=True)


# ------------------ PROJECT ------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 🔥 Relationships
    files = db.relationship('File', backref='project', lazy=True)
    collaborators = db.relationship('ProjectCollaborator', backref='project', lazy=True)


# ------------------ FILE (VERSION CONTROL) ------------------
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(200))
    version = db.Column(db.Integer)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    commit_message = db.Column(db.String(200))
    original_name = db.Column(db.String(200))

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------ COLLABORATORS ------------------
class ProjectCollaborator(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    role = db.Column(db.String(50), default="collaborator")

    user = db.relationship('User')


# ------------------ CANVAS ------------------
class Canvas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text)


# ------------------ CHAT MESSAGE ------------------
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    username = db.Column(db.String(100))
    project_id = db.Column(db.Integer)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    file = db.Column(db.String(200))


# ------------------ DRIVE FILE (USER STORAGE) ------------------
class DriveFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(300))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    uploaded_at = db.Column(db.DateTime, default=db.func.now())
#-----------AI Project tracker-----------
class AIProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    prompt = db.Column(db.Text)

    tasks = db.Column(db.Text)  # store JSON string
    progress = db.Column(db.Integer, default=0)