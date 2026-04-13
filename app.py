from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from config import Config
from models import db, User, Project, File, ProjectCollaborator,DriveFile
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__)
online_users = {}   # { project_id: { socket_id: username } }
app.config.from_object(Config)
socketio = SocketIO(app)

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
    owned_projects = Project.query.filter_by(user_id=current_user.id).all()

    collaborations = ProjectCollaborator.query.filter_by(
        user_id=current_user.id
    ).all()

    collaborated_projects = [
        Project.query.get(c.project_id) for c in collaborations
    ]

    all_projects = list({p.id: p for p in owned_projects + collaborated_projects}.values())

    return render_template("dashboard.html", projects=all_projects)
#----------------------------------tool-------------------------------------
@app.route('/project/<int:project_id>/tools')
@login_required

def tools(project_id):
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

    return render_template("tools.html", project=project)
#--------canva----------------------------------------------------------
from models import Canvas

@app.route('/project/<int:project_id>/canvas', methods=['GET', 'POST'])
@login_required
def canvas(project_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # Access check
    is_owner = project.user_id == current_user.id
    collaborator = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=current_user.id
    ).first()

    if not is_owner and not collaborator:
        return "Access Denied 🚫"



    # -------- SAVE --------
    if request.method == "POST":
        data = request.json.get("data")

        canvas = Canvas.query.filter_by(project_id=project_id).first()

        if canvas:
            canvas.data = data
        else:
            canvas = Canvas(project_id=project_id, data=data)
            db.session.add(canvas)

        db.session.commit()
        return {"status": "saved"}

    # -------- LOAD --------
    canvas = Canvas.query.filter_by(project_id=project_id).first()
    canvas_data = canvas.data if canvas else None

    return render_template("canvas.html", project=project, canvas_data=canvas_data)

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
@app.route('/drive_download/<int:file_id>')
@login_required
def drive_download(file_id):
    file = DriveFile.query.get(file_id)

    return send_from_directory(
        os.path.dirname(file.filepath),
        os.path.basename(file.filepath),
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

        return redirect(url_for('project', project_id=project_id))

    else:
       return "User not found ❌"

#-------------------remove collaborators -----------
@app.route('/remove_collaborator/<int:project_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_collaborator(project_id, user_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # 🔒 Only owner can remove
    if project.user_id != current_user.id:
        return "Only owner can remove collaborators 🚫"

    collab = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()

    if not collab:
        return "Collaborator not found ❌"

    db.session.delete(collab)
    db.session.commit()

    return redirect(url_for('project', project_id=project_id))

#-------------------adding socket event ---------------------------------
@socketio.on('join')
def handle_join(data):
    project_id = str(data['project_id'])
    username = data['username']
    sid = request.sid   # 🔥 UNIQUE SOCKET ID

    join_room(project_id)

    if project_id not in online_users:
        online_users[project_id] = {}

    online_users[project_id][sid] = username

    # Send updated list
    users = list(online_users[project_id].values())
    emit('update_users', users, room=project_id)
    #--------disconnect---------
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid

    for project_id in list(online_users.keys()):
        if sid in online_users[project_id]:
            del online_users[project_id][sid]

            users = list(online_users[project_id].values())
            emit('update_users', users, room=project_id)
    #-----------fix real time draw-----
@socketio.on('draw')
def handle_draw(data):
    project_id = str(data['project_id'])
    emit('draw', data, room=project_id, include_self=False)
    #-------------curroser mover---------
@socketio.on('cursor_move')
def handle_cursor(data):
    project_id = str(data['project_id'])
    emit('cursor_move', data, room=project_id, include_self=False)
#-------------------adding routes for chat system -------------------------
@app.route("/chat/<int:project_id>")
@login_required
def chat(project_id):
    project = Project.query.get(project_id)

    messages = Message.query.filter_by(project_id=project_id).all()

    return render_template("chat.html", project=project, messages=messages)
         # ------------------ CHAT SYSTEM ------------------
from models import Message

@socketio.on('send_message')
def handle_send_message(data):
    project_id = data['project_id']

    msg = Message(
        content=data.get('message'),
        username=data['username'],
        project_id=project_id,
        file=data.get('file')
    )
    db.session.add(msg)
    db.session.commit()

    emit('receive_message', {
        'message': msg.content,
        'username': msg.username,
        'time': msg.timestamp.strftime("%I:%M %p"),
        'file': msg.file
    }, room=str(project_id))
    #---------------------Adding typing indicitor-----------------
@socketio.on('typing')
def handle_typing(data):
    project_id = str(data['project_id'])

    emit('show_typing', {
        'username': data['username']
    }, room=project_id, include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    project_id = str(data['project_id'])

    emit('hide_typing', {
        'username': data['username']
    }, room=project_id)
#-------------------Adding route for file upload --------------
@app.route('/upload_chat_file/<int:project_id>', methods=['POST'])
@login_required
def upload_chat_file(project_id):
    file = request.files['file']

    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return {"filename": filename}
#-----------------delete project -----------
@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    # 🔍 Get project
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # 🔒 Only owner can delete
    if project.user_id != current_user.id:
        return "Only owner can delete this project 🚫"

    # 🧹 Delete related collaborators
    ProjectCollaborator.query.filter_by(project_id=project_id).delete()

    # 🧹 Delete related files
    File.query.filter_by(project_id=project_id).delete()

    # 🧹 Delete canvas data (IMPORTANT if you added Canvas model)
    try:
        from models import Canvas
        Canvas.query.filter_by(project_id=project_id).delete()
    except:
        pass  # ignore if not exists

    # 🗑 Delete project
    db.session.delete(project)
    db.session.commit()

    return redirect(url_for('dashboard'))

#-------------collaborators managers----------
@app.route('/project/<int:project_id>/collaborators')
@login_required
def collaborator_manager(project_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # Access check
    is_owner = project.user_id == current_user.id
    collab = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=current_user.id
    ).first()

    if not is_owner and not collab:
        return "Access Denied 🚫"

    collaborators = ProjectCollaborator.query.filter_by(project_id=project_id).all()

    return render_template("collaborators.html", project=project, collaborators=collaborators)
#-------------------adding route for the drive 
@app.route('/project/<int:project_id>/drive', methods=['GET', 'POST'])
@login_required
def drive(project_id):
    project = Project.query.get(project_id)

    if not project:
        return "Project not found ❌"

    # access control
    is_owner = project.user_id == current_user.id
    collab = ProjectCollaborator.query.filter_by(
        project_id=project_id,
        user_id=current_user.id
    ).first()

    if not is_owner and not collab:
        return "Access Denied 🚫"

    # 📤 UPLOAD
    if request.method == "POST":
        file = request.files['file']

        filename = file.filename
        filepath = os.path.join("uploads/drive", filename)

        os.makedirs("uploads/drive", exist_ok=True)
        file.save(filepath)

        new_file = DriveFile(
            filename=filename,
            filepath=filepath,
            user_id=current_user.id,
            project_id=project_id
        )

        db.session.add(new_file)
        db.session.commit()

    files = DriveFile.query.filter_by(project_id=project_id).all()

    return render_template("drive.html", project=project, files=files)
# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)