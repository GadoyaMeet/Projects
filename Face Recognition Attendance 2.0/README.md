# Face Recognition Attendance 2.0

A complete, modern, web-based Face Recognition Attendance System built with Flask, OpenCV, and dlib. This unified application allows you to register users, train a 128-dimensional face recognition model, take real-time attendance via webcam, and view historical records—all from a sleek, dark-themed web browser interface.


## Prerequisites

- **Python 3.10 (Highly Recommended)**: `dlib` does not currently provide pre-built installation wheels for Python 3.12 or 3.13 on Windows. Using Python 3.10 allows `pip` to install `dlib` instantly without compilation errors.
- If you are using Python 3.11 or higher, you **must** have **CMake** and **Visual Studio C++ Build Tools** installed on your system to compile `dlib` from source, otherwise the installation will fail.

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd "Face Recognition Attendance 2.0"
   ```

2. **Create and activate a virtual environment**:
   Make sure you create the environment using Python 3.10 (or use your existing Python 3.10 environment) to avoid `dlib` installation errors.
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   > *Note: Installing `dlib` might take a few minutes as it compiles C++ code under the hood.*

4. **Ensure `dlib` models are present**:
   The project requires two pre-trained models inside the `data/data_dlib/` folder:
   - `shape_predictor_68_face_landmarks.dat`
   - `dlib_face_recognition_resnet_model_v1.dat`

## Usage

1. **Start the Flask Application**:
   ```bash
   python app.py
   ```
2. **Access the Application**:
   Open your web browser and navigate to `http://localhost:5000`.

3. **Workflow**:
   - Go to **Register** to add a new person. Enter their name and look at the camera.
   - Go to the **Dashboard** and click **Train Models** to extract the features for the newly registered faces.
   - Go to **Take Attendance** to start logging attendance.
   - Go to **View Records** to check the attendance database by date.

## Directory Structure
```
Face Recognition Attendance 2.0/
├── app.py                     # Main Flask application and routes
├── camera.py                  # OpenCV video capture and frame processing logic
├── face_utils.py              # Dlib feature extraction and database logic
├── requirements.txt           # Project dependencies
├── attendance.db              # SQLite database (generated automatically)
├── data/
│   ├── data_dlib/             # Pre-trained dlib .dat models
│   ├── data_faces_from_camera/# Directory where captured faces are saved
│   └── features_all.csv       # Extracted 128D features dataset
├── static/
│   └── css/                   # Custom stylesheets
└── templates/                 # HTML templates
    ├── base.html              # Base layout
    ├── index.html             # Dashboard
    ├── register.html          # Registration UI
    ├── attendance_live.html   # Live recognition UI
    └── view_attendance.html   # Records viewing UI
```

## Acknowledgments
Uses the amazing [dlib](http://dlib.net/) C++ library for state-of-the-art face recognition and [OpenCV](https://opencv.org/) for computer vision.
