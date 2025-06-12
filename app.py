from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session
from flask_talisman import Talisman
import os
import time
import json
import qrcode
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from auth_db import init_db, verify_user

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Enable HTTPS but disable content security policy for development
Talisman(app, force_https=False, content_security_policy=None)

# Set upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
init_db()

# Add a route to serve uploaded files
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load rooms from JSON file or create new if not exists
ROOMS_FILE = 'rooms.json'

def load_rooms():
    if os.path.exists(ROOMS_FILE):
        with open(ROOMS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('rooms', []), data.get('slides', {}), data.get('last_updates', {})
    return [], {}, {}

def save_rooms(rooms, slides, last_updates):
    with open(ROOMS_FILE, 'w') as f:
        json.dump({
            'rooms': rooms,
            'slides': slides,
            'last_updates': last_updates
        }, f)

# Initialize rooms, slides, and last_updates
rooms, slides, last_updates = load_rooms()

# Create default rooms if none exist
if not rooms:
    default_rooms = ['pid1', 'pid2', 'pid3', 'pid4']
    for room in default_rooms:
        rooms.append(room)
        slides[room] = []
        last_updates[room] = time.time()
    save_rooms(rooms, slides, last_updates)

def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Route for the index page (room management page)
@app.route('/', methods=['GET', 'POST'])
def index():
    view_mode = request.args.get('view')
    if view_mode == 'public':
        authenticated = False
    else:
        if not check_auth():
            return redirect(url_for('login'))
        authenticated = True

    if request.method == 'POST':
        room_name = request.form.get('room_name')
        if room_name and room_name not in rooms:
            rooms.append(room_name)
            slides[room_name] = []
            last_updates[room_name] = time.time()
            save_rooms(rooms, slides, last_updates)
            room_url = url_for('room', room_id=room_name, _external=True)
            qr_code = generate_qr_code(room_url)
            return render_template('room_created.html', room_name=room_name, room_url=room_url, qr_code=qr_code)
    return render_template('index.html', rooms=rooms, slides=slides, authenticated=authenticated, username=session.get('username'))

# Route to view a specific room (view-only mode)
@app.route('/room/<room_id>')
def room(room_id):
    if room_id not in rooms:
        return "Room not found", 404
    return render_template('fullscreen.html', room_id=room_id, slides=slides[room_id])

def check_auth():
    return session.get('logged_in')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if verify_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/room/<room_id>/edit')
def room_edit(room_id):
    if not check_auth():
        return redirect(url_for('login'))
    if room_id not in rooms:
        return "Room not found", 404
    room_url = url_for('room', room_id=room_id, _external=True)
    qr_code = generate_qr_code(room_url)
    return render_template('roomedit.html', room_id=room_id, slides=slides[room_id], edit_mode=True, room_url=room_url, qr_code=qr_code)

# API endpoint to check for updates
@app.route('/api/check_updates/<room_id>')
def check_updates(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404
    
    client_timestamp = float(request.args.get('timestamp', 0)) / 1000  # Convert from JS milliseconds to seconds
    server_timestamp = last_updates[room_id]
    
    # If the server's last update is newer than the client's timestamp, there are updates
    has_updates = server_timestamp > client_timestamp
    
    return jsonify({
        "hasUpdates": has_updates,
        "serverTime": server_timestamp * 1000  # Convert back to JS milliseconds
    })

# Route to upload a slide
@app.route('/upload/<room_id>', methods=['POST'])
def upload_slide(room_id):
    if not check_auth():
        return redirect(url_for('login'))
    if room_id not in rooms:
        return "Room not found", 404
   
    if 'file' not in request.files:
        return redirect(request.url)
   
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('room_edit', room_id=room_id))
   
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Ensure filename is unique to avoid overwriting existing slides
        if os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{name}_{counter}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                counter += 1
        file.save(filepath)
        # Store the path starting with /static/
        relative_path = f'/static/uploads/{filename}'
        print(f"Adding slide with path: {relative_path}")  # Debug print
        
        if room_id not in slides:
            slides[room_id] = []
        
        slides[room_id].append(relative_path)
        last_updates[room_id] = time.time()
        save_rooms(rooms, slides, last_updates)
        print(f"Current slides for room {room_id}: {slides[room_id]}")  # Debug print
   
    return redirect(url_for('room_edit', room_id=room_id))

@app.route('/delete_slide/<room_id>/<int:slide_index>', methods=['POST'])
def delete_slide(room_id, slide_index):
    if not check_auth():
        return redirect(url_for('login'))
    if room_id not in rooms or slide_index < 0 or slide_index >= len(slides[room_id]):
        return "Slide not found", 404
   
    slide_path = slides[room_id][slide_index]
    try:
        # Check if slide is used in other rooms before deleting the file
        used_elsewhere = False
        for r in rooms:
            if r != room_id and slide_path in slides[r]:
                used_elsewhere = True
                break
       
        # Only delete the file if it's not used in other rooms
        if not used_elsewhere:
            # Convert back to filesystem path
            fs_path = slide_path[1:] if slide_path.startswith('/') else slide_path
            if os.path.exists(fs_path):
                os.remove(fs_path)
       
        # Remove from this room's slides list
        slides[room_id].pop(slide_index)
        
        # Update the last update time for this room
        last_updates[room_id] = time.time()
        save_rooms(rooms, slides, last_updates)
    except Exception as e:
        return str(e), 500
   
    return redirect(url_for('room_edit', room_id=room_id))

# Route to share a slide across all rooms
@app.route('/share_slide/<room_id>/<int:slide_index>', methods=['POST'])
def share_slide(room_id, slide_index):
    if not check_auth():
        return redirect(url_for('login'))
    if room_id not in rooms or slide_index >= len(slides[room_id]):
        return "Slide not found", 404
   
    slide_path = slides[room_id][slide_index]
    # Add the slide to all other rooms
    for room in rooms:
        if room != room_id and slide_path not in slides[room]:
            slides[room].append(slide_path)
            # Update the last update time for rooms that received the slide
            last_updates[room] = time.time()
    save_rooms(rooms, slides, last_updates)
   
    return redirect(url_for('room_edit', room_id=room_id))

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5006))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
else:
    # Production Gunicorn server
    # Make sure uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
