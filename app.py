from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from config import Config
from models import db, User, Project, File, ProjectCollaborator
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------ HOME ------------------
@app.route('/')
def index():
    return render_template("index.html")


# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")


# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username")).first()

        if user and check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template("login.html")


# ------------------ LOGOUT ------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
@login_required
def dashboard():
        
        
   # Projects owned by user
        owned_projects = Project.query.filter_by(user_id=current_user.id).all()

# Projects where user is collaborator
        collaborations = ProjectCollaborator.query.filter_by(user_id=current_user.id).all()

        collab_projects = [Project.query.get(c.project_id) for c in collaborations]

# Combine both
        projects = owned_projects + collab_projects
        return render_template("dashboard.html", projects=projects)


# ------------------ CREATE PROJECT ------------------
@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == "POST":
        name = request.form.get("name")

        project = Project(name=name, user_id=current_user.id)
        db.session.add(project)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template("create_project.html")


# ------------------ PROJECT PAGE ------------------
@app.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # Access control
    is_owner = project.user_id == current_user.id

    collaborator = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=current_user.id
    ).first()

    if not is_owner and not collaborator:
        return "Access Denied 🚫"

    files = File.query.filter_by(project_id=project_id).all()
    collaborators = ProjectCollaborator.query.filter_by(project_id=project_id).all()

    # -------- FILE UPLOAD --------
    if request.method == "POST":
        file = request.files['file']
        message = request.form.get("message")

        name, ext = os.path.splitext(file.filename)

        existing_files = File.query.filter_by(
            project_id=project_id,
            original_name=name
        ).all()

        version = len(existing_files) + 1
        new_filename = f"{name}_v{version}{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)

        new_file = File(
            filename=new_filename,
            version=version,
            project_id=project_id,
            commit_message=message,
            original_name=name
        )

        db.session.add(new_file)
        db.session.commit()

        return redirect(url_for('project', project_id=project_id))

    return render_template("project.html", project=project, files=files,collaborators=collaborators)


# ------------------ DOWNLOAD ------------------
@app.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )


# ------------------ ADD COLLABORATOR ------------------
@app.route('/add_collaborator/<int:project_id>', methods=['POST'])
@login_required
def add_collaborator(project_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # Only owner can add collaborators
    if project.user_id != current_user.id:
        return "Only owner can add collaborators 🚫"

    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()

    if user:
        existing = ProjectCollaborator.query.filter_by(
            user_id=user.id,
            project_id=project_id
        ).first()

        if existing:
           return "User already a collaborator ⚠️"

        collab = ProjectCollaborator(
           user_id=user.id,
           project_id=project_id
        )
        db.session.add(collab)
        db.session.commit()

        return "Collaborator added successfully ✅"

    else:
       return "User not found ❌"

    return redirect(url_for('project', project_id=project_id))


# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)