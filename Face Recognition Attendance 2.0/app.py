from flask import Flask, render_template, request, Response, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime
from face_utils import init_db, train_model, DB_PATH
from camera import VideoCamera

app = Flask(__name__)
app.secret_key = 'super_secret_key_2.0'

# Initialize database
init_db()

# Global camera instance (Note: in a real prod app with multiple users, this is problematic, but fine for local run)
# We will instantiate lazily
camera = None

def get_camera():
    global camera
    if camera is None:
        camera = VideoCamera()
    return camera

def release_camera_internal():
    global camera
    if camera is not None:
        try:
            if camera.video.isOpened():
                camera.video.release()
        except:
            pass
        camera = None

def gen():
    cam = get_camera()
    try:
        while True:
            # If camera was released externally, break
            if camera is None:
                break
            frame = cam.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                break
    except GeneratorExit:
        # Client disconnected from the stream
        release_camera_internal()
    finally:
        release_camera_internal()

@app.route('/')
def index():
    release_camera_internal()
    return render_template('index.html')

@app.route('/register', methods=['GET'])
def register():
    cam = get_camera()
    cam.taking_attendance = False
    return render_template('register.html')

@app.route('/api/start_registration', methods=['POST'])
def start_registration():
    name = request.json.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'})
    
    cam = get_camera()
    cam.start_registration(name)
    return jsonify({'success': True})

@app.route('/api/registration_status')
def registration_status():
    cam = get_camera()
    return jsonify({
        'registering': cam.registering,
        'complete': cam.register_complete,
        'count': cam.capture_count,
        'max': cam.max_captures
    })

@app.route('/api/release_camera', methods=['POST'])
def release_camera():
    release_camera_internal()
    return jsonify({'success': True})

@app.route('/api/train', methods=['POST'])
def train():
    success, message = train_model()
    # Reload known faces in camera after training
    global camera
    if camera is not None:
        camera.reload_known_faces()
    return jsonify({'success': success, 'message': message})

@app.route('/take_attendance')
def take_attendance():
    cam = get_camera()
    cam.registering = False
    cam.taking_attendance = True
    return render_template('attendance_live.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    selected_date = ""
    attendance_data = []
    no_data = False
    
    if request.method == 'POST':
        selected_date = request.form.get('selected_date')
        if not selected_date:
            flash("Please select a valid date.", "warning")
            return redirect(url_for('view_attendance'))
            
        try:
            selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
            formatted_date = selected_date_obj.strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, time FROM attendance WHERE date = ?", (formatted_date,))
            attendance_data = cursor.fetchall()
            conn.close()
            
            if not attendance_data:
                no_data = True
                
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for('view_attendance'))
            
    return render_template('view_attendance.html', selected_date=selected_date, attendance_data=attendance_data, no_data=no_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
