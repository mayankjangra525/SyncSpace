from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

from datetime import datetime

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(200))
    version = db.Column(db.Integer)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    commit_message = db.Column(db.String(200))
    original_name = db.Column(db.String(200))

    # 🔥 ADD THIS
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class ProjectCollaborator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    role = db.Column(db.String(50), default="collaborator")
    user = db.relationship('User')
class Canvas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text)

from datetime import datetime

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    username = db.Column(db.String(100))
    project_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ FIX
    file = db.Column(db.String(200))
class DriveFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(300))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    uploaded_at = db.Column(db.DateTime, default=db.func.now())
files = db.relationship('File', backref='project')