import cv2
import dlib
import numpy as np
import time
import os
from face_utils import PATH_IMAGES_FROM_CAMERA, load_known_faces, euclidean_distance, mark_attendance

class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')
        self.face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")
        
        # State for registration
        self.registering = False
        self.person_name = ""
        self.person_dir = ""
        self.capture_count = 0
        self.max_captures = 10
        self.last_capture_time = 0
        self.register_complete = False

        # State for attendance
        self.taking_attendance = False
        self.process_this_frame = 0
        self.face_names, self.face_features = load_known_faces()

    def __del__(self):
        self.video.release()
        
    def start_registration(self, name):
        self.person_name = name
        self.capture_count = 0
        self.register_complete = False
        
        # Find next folder index
        existing_folders = [f for f in os.listdir(PATH_IMAGES_FROM_CAMERA) if os.path.isdir(os.path.join(PATH_IMAGES_FROM_CAMERA, f))]
        nums = [int(f.split('_')[1]) for f in existing_folders if f.startswith("person_") and f.split('_')[1].isdigit()]
        next_idx = max(nums) + 1 if nums else 1
        
        name_suffix = f"_{self.person_name.replace(' ', '_')}"
        self.person_dir = os.path.join(PATH_IMAGES_FROM_CAMERA, f"person_{next_idx}{name_suffix}")
        os.makedirs(self.person_dir, exist_ok=True)
        
        self.registering = True
        
    def reload_known_faces(self):
        self.face_names, self.face_features = load_known_faces()

    def get_frame(self):
        ret, frame = self.video.read()
        if not ret:
            return None
            
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
        self.process_this_frame += 1
        
        display_frame = frame.copy()
        font_scale = max(0.6, w / 1000.0) # Scale font size relative to width
        thickness = max(2, int(w / 400))
        
        if self.registering:
            cv2.putText(display_frame, f"Registering: {self.person_name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 0, 0), thickness)
            cv2.putText(display_frame, f"Captures: {self.capture_count}/{self.max_captures}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 0, 0), thickness)
            
            # Use small frame for blazing fast detection
            small_rgb = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
            small_faces = self.detector(small_rgb, 0)
            
            if len(small_faces) == 1:
                # scale coordinates back up
                x1, y1, x2, y2 = int(small_faces[0].left()*2), int(small_faces[0].top()*2), int(small_faces[0].right()*2), int(small_faces[0].bottom()*2)
                cv2.rectangle(display_frame, (max(0, x1), max(0, y1)), (min(w, x2), min(h, y2)), (0, 255, 0), thickness)
                
                # Capture an image every 0.5 seconds
                current_time = time.time()
                if current_time - self.last_capture_time > 0.5 and self.capture_count < self.max_captures:
                    # Crop face
                    hh = int((y2 - y1) / 2)
                    ww = int((x2 - x1) / 2)
                    crop_y1 = max(0, y1 - hh)
                    crop_x1 = max(0, x1 - ww)
                    crop_y2 = min(h, y2 + hh)
                    crop_x2 = min(w, x2 + ww)
                    
                    face_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                    if face_crop.size > 0:
                        self.capture_count += 1
                        save_path = os.path.join(self.person_dir, f"img_face_{self.capture_count}.jpg")
                        cv2.imwrite(save_path, face_crop)
                        self.last_capture_time = current_time
                        
                if self.capture_count >= self.max_captures:
                    self.registering = False
                    self.register_complete = True
            else:
                cv2.putText(display_frame, "Please ensure exactly ONE face is visible", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
                
        elif self.taking_attendance:
            cv2.putText(display_frame, "Taking Attendance (Live)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            if not hasattr(self, 'last_faces_boxes'):
                self.last_faces_boxes = []
                
            # Only run heavy face recognition every 5 frames to dramatically improve FPS
            if self.process_this_frame % 5 == 0:
                small_rgb = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
                small_faces = self.detector(small_rgb, 0)
                self.last_faces_boxes = []
                
                for s_face in small_faces:
                    # Scale back up
                    face = dlib.rectangle(int(s_face.left()*2), int(s_face.top()*2), int(s_face.right()*2), int(s_face.bottom()*2))
                    x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                    
                    shape = self.predictor(rgb_frame, face)
                    face_descriptor = self.face_reco_model.compute_face_descriptor(rgb_frame, shape)
                    
                    min_dist = 9999
                    matched_name = "Unknown"
                    
                    for i in range(len(self.face_features)):
                        dist = euclidean_distance(face_descriptor, self.face_features[i])
                        if dist < min_dist:
                            min_dist = dist
                            matched_name = self.face_names[i]
                            
                    if min_dist < 0.4:
                        marked, t = mark_attendance(matched_name)
                        display_name = matched_name
                        color = (0, 255, 0)
                    else:
                        display_name = "Unknown"
                        color = (0, 0, 255)
                        
                    self.last_faces_boxes.append((x1, y1, x2, y2, display_name, color))
            
            # Draw the cached boxes for all frames to keep video smooth
            for (x1, y1, x2, y2, display_name, color) in self.last_faces_boxes:
                cv2.rectangle(display_frame, (max(0, x1), max(0, y1)), (min(w, x2), min(h, y2)), (255, 255, 255), thickness)
                cv2.putText(display_frame, display_name, (max(0, x1), min(h, y2 + 30)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

        ret, jpeg = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        return jpeg.tobytes()
