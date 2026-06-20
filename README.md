# Face Recognition Attendance System

This project is an end-to-end Face Recognition Attendance System. It provides functionalities to register users via a webcam, extract facial features using deep learning, perform real-time face recognition for attendance logging, and view attendance records through a web portal.

## Features

- **Face Registration (GUI):** A Tkinter-based application to capture and save user faces from a live camera feed.
- **Feature Extraction:** Uses `dlib`'s ResNet model to extract 128D face descriptors (embeddings) from the captured faces and saves them in a CSV database.
- **Real-Time Attendance Taking:** Monitors a camera feed, detects faces, compares them against the known database, and logs attendance into an SQLite database if a match is found.
- **Web Dashboard:** A Flask web application to query and view attendance logs for any specific date.

## Requirements

Ensure you have Python 3.7+ installed. Install the dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

*Note: Installing `dlib` might require you to have CMake and a C++ compiler installed on your system.*

## Workflow Demonstration

Follow these steps in order to use the system:

### Step 1: Register New Faces
Run the Tkinter GUI to capture face images for a new user.

```bash
python get_faces_from_camera_tkinter.py
```
1. Enter the person's name in the "Name" field.
2. Click **Input** to create their directory.
3. Look at the camera and click **Save Face** to capture a few photos of the person's face.
4. Close the application when done.

### Step 2: Extract Face Features
Once you have saved the face images, you need to extract their 128D features to build the "known faces" database.

```bash
python features_extraction_to_csv.py
```
This script will process all images in the `data/data_faces_from_camera/` directory, compute the average embeddings, and save the data to `data/features_all.csv`.

### Step 3: Take Attendance
Start the real-time face recognition script to log attendance.

```bash
python attendance_taker.py
```
This script opens the webcam, detects faces, matches them against the CSV database, and marks the recognized individuals as "Present" in the local `attendance.db` SQLite database. Press `q` to stop the camera.

### Step 4: View Attendance Logs
To view the recorded attendance, start the Flask web server.

```bash
python app.py
```
Open your web browser and go to `http://127.0.0.1:5000`. Use the date picker on the portal to select a date and fetch the attendance logs for that day.

## Project Structure

- `get_faces_from_camera_tkinter.py`: GUI for face registration.
- `features_extraction_to_csv.py`: Script to generate the face embeddings database.
- `attendance_taker.py`: Real-time face recognition and attendance logging script.
- `app.py`: Flask backend for the web portal.
- `templates/index.html`: Web interface for viewing attendance.
- `data/`: Contains saved face images, Dlib models, and the `features_all.csv` database.
- `attendance.db`: SQLite database storing attendance records.
