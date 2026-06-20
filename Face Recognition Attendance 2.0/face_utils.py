import os
import dlib
import csv
import numpy as np
import logging
import cv2
import sqlite3
import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)

# Paths
PATH_IMAGES_FROM_CAMERA = "data/data_faces_from_camera/"
FEATURES_SAVE_PATH = "data/features_all.csv"
DB_PATH = "attendance.db"

# Load Dlib models
# Make sure the data_dlib folder contains the required .dat files
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    table_name = "attendance"
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        name TEXT,
        time TEXT,
        date DATE,
        UNIQUE(name, date)
    )"""
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()

def return_128d_features(path_img):
    img_rd = cv2.imread(path_img)
    if img_rd is None:
        return None
    if img_rd.dtype != np.uint8:
        img_rd = img_rd.astype(np.uint8)
    if len(img_rd.shape) == 2:
        img_rd = cv2.cvtColor(img_rd, cv2.COLOR_GRAY2RGB)
    elif img_rd.shape[2] == 3:
        img_rd = cv2.cvtColor(img_rd, cv2.COLOR_BGR2RGB)
    else:
        return None

    faces = detector(img_rd, 1)
    if len(faces) == 0:
        return None

    shape = predictor(img_rd, faces[0])
    face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
    return np.array(face_descriptor)

def return_features_mean_personX(path_face_personX):
    features_list = []
    photo_list = os.listdir(path_face_personX)
    if not photo_list:
        return None

    for photo in photo_list:
        img_path = os.path.join(path_face_personX, photo)
        features_128d = return_128d_features(img_path)
        if features_128d is not None:
            features_list.append(features_128d)

    if features_list:
        return np.mean(features_list, axis=0)
    else:
        return None

def train_model():
    """Extract features from all images in the folder and save to CSV."""
    if not os.path.exists(PATH_IMAGES_FROM_CAMERA):
        os.makedirs(PATH_IMAGES_FROM_CAMERA, exist_ok=True)
        
    person_list = sorted(os.listdir(PATH_IMAGES_FROM_CAMERA))
    if not person_list:
        return False, "No faces registered yet."
        
    with open(FEATURES_SAVE_PATH, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for person in person_list:
            person_dir = os.path.join(PATH_IMAGES_FROM_CAMERA, person)
            if not os.path.isdir(person_dir):
                continue
                
            features_mean = return_features_mean_personX(person_dir)
            if features_mean is None:
                continue

            if len(person.split('_', 2)) == 2:
                person_name = person
            else:
                person_name = person.split('_', 2)[-1]

            row = [person_name] + list(map(float, features_mean))
            writer.writerow(row)
            logging.info(f"Saved features for: {person_name}")

    return True, "Training completed successfully."

def load_known_faces():
    face_features_known_list = []
    face_name_known_list = []
    if os.path.exists(FEATURES_SAVE_PATH):
        if os.path.getsize(FEATURES_SAVE_PATH) == 0:
            return [], []
        try:
            csv_rd = pd.read_csv(FEATURES_SAVE_PATH, header=None)
            for i in range(csv_rd.shape[0]):
                features_someone_arr = []
                face_name_known_list.append(csv_rd.iloc[i][0])
                for j in range(1, 129):
                    val = csv_rd.iloc[i][j]
                    features_someone_arr.append(float(val) if not pd.isna(val) else 0.0)
                face_features_known_list.append(features_someone_arr)
            return face_name_known_list, face_features_known_list
        except Exception as e:
            logging.error(f"Error loading features: {e}")
            return [], []
    return [], []

def mark_attendance(name):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM attendance WHERE name = ? AND date = ?", (name, current_date))
    existing = cursor.fetchone()
    marked_just_now = False
    
    if not existing:
        try:
            cursor.execute("INSERT INTO attendance (name, time, date) VALUES (?, ?, ?)",
                           (name, current_time, current_date))
            conn.commit()
            marked_just_now = True
        except sqlite3.IntegrityError:
            pass
            
    conn.close()
    return marked_just_now, current_time

def euclidean_distance(feature_1, feature_2):
    feature_1 = np.array(feature_1)
    feature_2 = np.array(feature_2)
    return np.sqrt(np.sum(np.square(feature_1 - feature_2)))
