# import dlib
# import numpy as np
# import cv2
# import os
# import shutil
# import time
# import logging
# import tkinter as tk
# from tkinter import font as tkFont
# from PIL import Image, ImageTk

# # Use frontal face detector of Dlib
# detector = dlib.get_frontal_face_detector()


# class Face_Register:
#     def __init__(self):

#         self.current_frame_faces_cnt = 0  #  cnt for counting faces in current frame
#         self.existing_faces_cnt = 0  # cnt for counting saved faces
#         self.ss_cnt = 0  #  cnt for screen shots

#         # Tkinter GUI
#         self.win = tk.Tk()
#         self.win.title("Face Register")

#         # PLease modify window size here if needed
#         self.win.geometry("1000x500")

#         # GUI left part
#         self.frame_left_camera = tk.Frame(self.win)
#         self.label = tk.Label(self.win)
#         self.label.pack(side=tk.LEFT)
#         self.frame_left_camera.pack()

#         # GUI right part
#         self.frame_right_info = tk.Frame(self.win)
#         self.label_cnt_face_in_database = tk.Label(self.frame_right_info, text=str(self.existing_faces_cnt))
#         self.label_fps_info = tk.Label(self.frame_right_info, text="")
#         self.input_name = tk.Entry(self.frame_right_info)
#         self.input_name_char = ""
#         self.label_warning = tk.Label(self.frame_right_info)
#         self.label_face_cnt = tk.Label(self.frame_right_info, text="Faces in current frame: ")
#         self.log_all = tk.Label(self.frame_right_info)

#         self.font_title = tkFont.Font(family='Helvetica', size=20, weight='bold')
#         self.font_step_title = tkFont.Font(family='Helvetica', size=15, weight='bold')
#         self.font_warning = tkFont.Font(family='Helvetica', size=15, weight='bold')

#         self.path_photos_from_camera = "data/data_faces_from_camera/"
#         self.current_face_dir = ""
#         self.font = cv2.FONT_ITALIC

#         # Current frame and face ROI position
#         self.current_frame = np.ndarray
#         self.face_ROI_image = np.ndarray
#         self.face_ROI_width_start = 0
#         self.face_ROI_height_start = 0
#         self.face_ROI_width = 0
#         self.face_ROI_height = 0
#         self.ww = 0
#         self.hh = 0

#         self.out_of_range_flag = False
#         self.face_folder_created_flag = False

#         # FPS
#         self.frame_time = 0
#         self.frame_start_time = 0
#         self.fps = 0
#         self.fps_show = 0
#         self.start_time = time.time()

#         self.cap = cv2.VideoCapture(0)  # Get video stream from camera

#         # self.cap = cv2.VideoCapture("test.mp4")   # Input local video

#     #  Delete old face folders
#     def GUI_clear_data(self):
#         #  "/data_faces_from_camera/person_x/"...
#         folders_rd = os.listdir(self.path_photos_from_camera)
#         for i in range(len(folders_rd)):
#             shutil.rmtree(self.path_photos_from_camera + folders_rd[i])
#         if os.path.isfile("data/features_all.csv"):
#             os.remove("data/features_all.csv")
#         self.label_cnt_face_in_database['text'] = "0"
#         self.existing_faces_cnt = 0
#         self.log_all["text"] = "Face images and `features_all.csv` removed!"

#     def GUI_get_input_name(self):
#         self.input_name_char = self.input_name.get()
#         self.create_face_folder()
#         self.label_cnt_face_in_database['text'] = str(self.existing_faces_cnt)

#     def GUI_info(self):
#         tk.Label(self.frame_right_info,
#                  text="Face register",
#                  font=self.font_title).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=2, pady=20)

#         tk.Label(self.frame_right_info, text="FPS: ").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
#         self.label_fps_info.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

#         tk.Label(self.frame_right_info, text="Faces in database: ").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
#         self.label_cnt_face_in_database.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

#         tk.Label(self.frame_right_info,
#                  text="Faces in current frame: ").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
#         self.label_face_cnt.grid(row=3, column=2, columnspan=3, sticky=tk.W, padx=5, pady=2)

#         self.label_warning.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)

#         # Step 1: Clear old data
#         tk.Label(self.frame_right_info,
#                  font=self.font_step_title,
#                  text="Step 1: Clear face photos").grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)
#         tk.Button(self.frame_right_info,
#                   text='Clear',
#                   command=self.GUI_clear_data).grid(row=6, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)

#         # Step 2: Input name and create folders for face
#         tk.Label(self.frame_right_info,
#                  font=self.font_step_title,
#                  text="Step 2: Input name").grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)

#         tk.Label(self.frame_right_info, text="Name: ").grid(row=8, column=0, sticky=tk.W, padx=5, pady=0)
#         self.input_name.grid(row=8, column=1, sticky=tk.W, padx=0, pady=2)

#         tk.Button(self.frame_right_info,
#                   text='Input',
#                   command=self.GUI_get_input_name).grid(row=8, column=2, padx=5)

#         # Step 3: Save current face in frame
#         tk.Label(self.frame_right_info,
#                  font=self.font_step_title,
#                  text="Step 3: Save face image").grid(row=9, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)

#         tk.Button(self.frame_right_info,
#                   text='Save current face',
#                   command=self.save_current_face).grid(row=10, column=0, columnspan=3, sticky=tk.W)

#         # Show log in GUI
#         self.log_all.grid(row=11, column=0, columnspan=20, sticky=tk.W, padx=5, pady=20)

#         self.frame_right_info.pack()

#     # Mkdir for saving photos and csv
#     def pre_work_mkdir(self):
#         # Create folders to save face images and csv
#         if os.path.isdir(self.path_photos_from_camera):
#             pass
#         else:
#             os.mkdir(self.path_photos_from_camera)

#     # Start from person_x+1
#     def check_existing_faces_cnt(self):
#         if os.listdir("data/data_faces_from_camera/"):
#             # Get the order of latest person
#             person_list = os.listdir("data/data_faces_from_camera/")
#             person_num_list = []
#             for person in person_list:
#                 person_order = person.split('_')[1].split('_')[0]
#                 person_num_list.append(int(person_order))
#             self.existing_faces_cnt = max(person_num_list)

#         # Start from person_1
#         else:
#             self.existing_faces_cnt = 0

#     # Update FPS of Video stream
#     def update_fps(self):
#         now = time.time()
#         #  Refresh fps per second
#         if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
#             self.fps_show = self.fps
#         self.start_time = now
#         self.frame_time = now - self.frame_start_time
#         self.fps = 1.0 / self.frame_time
#         self.frame_start_time = now

#         self.label_fps_info["text"] = str(self.fps.__round__(2))

#     def create_face_folder(self):
#         #  Create the folders for saving faces
#         self.existing_faces_cnt += 1
#         if self.input_name_char:
#             self.current_face_dir = self.path_photos_from_camera + \
#                                     "person_" + str(self.existing_faces_cnt) + "_" + \
#                                     self.input_name_char
#         else:
#             self.current_face_dir = self.path_photos_from_camera + \
#                                     "person_" + str(self.existing_faces_cnt)
#         os.makedirs(self.current_face_dir)
#         self.log_all["text"] = "\"" + self.current_face_dir + "/\" created!"
#         logging.info("\n%-40s %s", "Create folders:", self.current_face_dir)

#         self.ss_cnt = 0  #  Clear the cnt of screen shots
#         self.face_folder_created_flag = True  # Face folder already created

#     def save_current_face(self):
#         if self.face_folder_created_flag:
#             if self.current_frame_faces_cnt == 1:
#                 if not self.out_of_range_flag:
#                     self.ss_cnt += 1
#                     #  Create blank image according to the size of face detected
#                     self.face_ROI_image = np.zeros((int(self.face_ROI_height * 2), self.face_ROI_width * 2, 3),
#                                                    np.uint8)
#                     for ii in range(self.face_ROI_height * 2):
#                         for jj in range(self.face_ROI_width * 2):
#                             self.face_ROI_image[ii][jj] = self.current_frame[self.face_ROI_height_start - self.hh + ii][
#                                 self.face_ROI_width_start - self.ww + jj]
#                     self.log_all["text"] = "\"" + self.current_face_dir + "/img_face_" + str(
#                         self.ss_cnt) + ".jpg\"" + " saved!"
#                     self.face_ROI_image = cv2.cvtColor(self.face_ROI_image, cv2.COLOR_BGR2RGB)

#                     cv2.imwrite(self.current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", self.face_ROI_image)
#                     logging.info("%-40s %s/img_face_%s.jpg", "Save into：",
#                                  str(self.current_face_dir), str(self.ss_cnt) + ".jpg")
#                 else:
#                     self.log_all["text"] = "Please do not out of range!"
#             else:
#                 self.log_all["text"] = "No face in current frame!"
#         else:
#             self.log_all["text"] = "Please run step 2!"

#     def get_frame(self):
#         try:
#             if self.cap.isOpened():
#                 ret, frame = self.cap.read()
#                 frame = cv2.resize(frame, (640,480))
#                 return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         except:
#             print("Error: No video input!!!")
        
#         return False, None

#     #  Main process of face detection and saving
#     def process(self):
#         ret, self.current_frame = self.get_frame()
        
#         # if not ret or self.current_frame is None or not isinstance(self.current_frame, np.ndarray):
#         #     print("Invalid frame: None or not ndarray")
#         #     self.win.after(20, self.process)
#         #     return  # Skip if camera failed

#         # # Ensure correct image format for dlib
#         # if self.current_frame.dtype != np.uint8:
#         #     self.current_frame = self.current_frame.astype(np.uint8)

#         # if len(self.current_frame.shape) != 3 or self.current_frame.shape[2] != 3:
#         #     print("Invalid frame shape")
#         #     self.win.after(20, self.process)
#         #     return

#         faces = detector(self.current_frame, 1)

        
#         # Get frame
#         if ret:
#             self.update_fps()
#             self.label_face_cnt["text"] = str(len(faces))
#             #  Face detected
#             if len(faces) != 0:
#                 #   Show the ROI of faces
#                 for k, d in enumerate(faces):
#                     self.face_ROI_width_start = d.left()
#                     self.face_ROI_height_start = d.top()
#                     #  Compute the size of rectangle box
#                     self.face_ROI_height = (d.bottom() - d.top())
#                     self.face_ROI_width = (d.right() - d.left())
#                     self.hh = int(self.face_ROI_height / 2)
#                     self.ww = int(self.face_ROI_width / 2)

#                     # If the size of ROI > 480x640
#                     if (d.right() + self.ww) > 640 or (d.bottom() + self.hh > 480) or (d.left() - self.ww < 0) or (
#                             d.top() - self.hh < 0):
#                         self.label_warning["text"] = "OUT OF RANGE"
#                         self.label_warning['fg'] = 'red'
#                         self.out_of_range_flag = True
#                         color_rectangle = (255, 0, 0)
#                     else:
#                         self.out_of_range_flag = False
#                         self.label_warning["text"] = ""
#                         color_rectangle = (255, 255, 255)
#                     self.current_frame = cv2.rectangle(self.current_frame,
#                                                        tuple([d.left() - self.ww, d.top() - self.hh]),
#                                                        tuple([d.right() + self.ww, d.bottom() + self.hh]),
#                                                        color_rectangle, 2)
#             self.current_frame_faces_cnt = len(faces)

#             # Convert PIL.Image.Image to PIL.Image.PhotoImage
#             img_Image = Image.fromarray(self.current_frame)
#             img_PhotoImage = ImageTk.PhotoImage(image=img_Image)
#             self.label.img_tk = img_PhotoImage
#             self.label.configure(image=img_PhotoImage)

#         # Refresh frame
#         self.win.after(20, self.process)

#     def run(self):
#         self.pre_work_mkdir()
#         self.check_existing_faces_cnt()
#         self.GUI_info()
#         self.process()
#         self.win.mainloop()


# def main():
#     logging.basicConfig(level=logging.INFO)
#     Face_Register_con = Face_Register()
#     Face_Register_con.run()


# if __name__ == '__main__':
#     main()


import dlib
import numpy as np
import cv2
import os
import shutil
import time
import logging
import tkinter as tk
from tkinter import font as tkFont
from PIL import Image, ImageTk

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Dlib detector
detector = dlib.get_frontal_face_detector()

class Face_Register:
    def __init__(self):
        self.current_frame_faces_cnt = 0
        self.existing_faces_cnt = 0
        self.ss_cnt = 0

        self.win = tk.Tk()
        self.win.title("Face Register")
        self.win.geometry("1000x500")

        # Layout
        self.frame_left_camera = tk.Frame(self.win)
        self.frame_right_info = tk.Frame(self.win)

        self.label = tk.Label(self.frame_left_camera)
        self.label.pack()
        self.frame_left_camera.pack(side=tk.LEFT)

        self.frame_right_info.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # GUI elements
        self.label_cnt_face_in_database = tk.Label(self.frame_right_info, text="0")
        self.label_fps_info = tk.Label(self.frame_right_info, text="0")
        self.input_name = tk.Entry(self.frame_right_info)
        self.input_name_char = ""
        self.label_warning = tk.Label(self.frame_right_info)
        self.label_face_cnt = tk.Label(self.frame_right_info, text="0")
        self.log_all = tk.Label(self.frame_right_info)

        self.font_title = tkFont.Font(family='Helvetica', size=20, weight='bold')
        self.font_step_title = tkFont.Font(family='Helvetica', size=15, weight='bold')

        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.current_face_dir = ""
        self.font = cv2.FONT_ITALIC

        self.current_frame = None
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0

        self.out_of_range_flag = False
        self.face_folder_created_flag = False

        self.frame_time = 0
        self.frame_start_time = time.time()
        self.fps = 0


        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logging.critical("Camera not accessible.")
            self.win.destroy()
            return

    def GUI_clear_data(self):
        if os.path.exists(self.path_photos_from_camera):
            shutil.rmtree(self.path_photos_from_camera)
            os.makedirs(self.path_photos_from_camera)
        if os.path.exists("data/features_all.csv"):
            os.remove("data/features_all.csv")
        self.label_cnt_face_in_database["text"] = "0"
        self.existing_faces_cnt = 0
        self.log_all["text"] = "Cleared all data."

    def GUI_get_input_name(self):
        self.input_name_char = self.input_name.get().strip()
        if not self.input_name_char:
            self.log_all["text"] = "Please enter a name."
            return
        self.create_face_folder()
        self.label_cnt_face_in_database["text"] = str(self.existing_faces_cnt)

    def GUI_info(self):
        row = 0
        tk.Label(self.frame_right_info, text="Face Register", font=self.font_title).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        tk.Label(self.frame_right_info, text="FPS:").grid(row=row, column=0, sticky=tk.W)
        self.label_fps_info.grid(row=row, column=1, sticky=tk.W)
        row += 1
        tk.Label(self.frame_right_info, text="Faces in database:").grid(row=row, column=0, sticky=tk.W)
        self.label_cnt_face_in_database.grid(row=row, column=1, sticky=tk.W)
        row += 1
        tk.Label(self.frame_right_info, text="Faces in current frame:").grid(row=row, column=0, sticky=tk.W)
        self.label_face_cnt.grid(row=row, column=1, sticky=tk.W)
        row += 1
        self.label_warning.grid(row=row, column=0, columnspan=2)
        row += 1
        tk.Label(self.frame_right_info, text="Step 1: Clear face photos", font=self.font_step_title).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        tk.Button(self.frame_right_info, text='Clear', command=self.GUI_clear_data).grid(row=row, column=0, sticky=tk.W)
        row += 1
        tk.Label(self.frame_right_info, text="Step 2: Input name", font=self.font_step_title).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        tk.Label(self.frame_right_info, text="Name:").grid(row=row, column=0, sticky=tk.W)
        self.input_name.grid(row=row, column=1)
        tk.Button(self.frame_right_info, text="Input", command=self.GUI_get_input_name).grid(row=row, column=2)
        row += 1
        tk.Label(self.frame_right_info, text="Step 3: Save face", font=self.font_step_title).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        tk.Button(self.frame_right_info, text='Save Face', command=self.save_current_face).grid(row=row, column=0, sticky=tk.W)
        row += 1
        self.log_all.grid(row=row, column=0, columnspan=3, pady=10)

    def pre_work_mkdir(self):
        os.makedirs(self.path_photos_from_camera, exist_ok=True)

    def check_existing_faces_cnt(self):
        folders = [f for f in os.listdir(self.path_photos_from_camera) if os.path.isdir(os.path.join(self.path_photos_from_camera, f))]
        nums = [int(f.split('_')[1]) for f in folders if f.startswith("person_") and f.split('_')[1].isdigit()]
        self.existing_faces_cnt = max(nums) if nums else 0

    def update_fps(self):
        now = time.time()
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time if self.frame_time != 0 else 0
        self.label_fps_info["text"] = f"{self.fps:.2f}"
        self.frame_start_time = now

    def create_face_folder(self):
        self.existing_faces_cnt += 1
        name_suffix = f"_{self.input_name_char.replace(' ', '_')}"
        self.current_face_dir = os.path.join(self.path_photos_from_camera, f"person_{self.existing_faces_cnt}{name_suffix}")
        os.makedirs(self.current_face_dir, exist_ok=True)
        self.ss_cnt = 0
        self.face_folder_created_flag = True
        self.log_all["text"] = f"Created folder: {self.current_face_dir}"

    def save_current_face(self):
        if not self.face_folder_created_flag:
            self.log_all["text"] = "Run Step 2 first."
            return
        if self.current_frame_faces_cnt != 1:
            self.log_all["text"] = "No face or multiple faces detected."
            return
        if self.out_of_range_flag:
            self.log_all["text"] = "Face is out of range."
            return

        self.ss_cnt += 1
        h1 = max(0, self.face_ROI_height_start - self.hh)
        w1 = max(0, self.face_ROI_width_start - self.ww)
        h2 = min(self.current_frame.shape[0], self.face_ROI_height_start + self.face_ROI_height + self.hh)
        w2 = min(self.current_frame.shape[1], self.face_ROI_width_start + self.face_ROI_width + self.ww)
        face_img = self.current_frame[h1:h2, w1:w2]

        save_path = os.path.join(self.current_face_dir, f"img_face_{self.ss_cnt}.jpg")
        cv2.imwrite(save_path, cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))
        self.log_all["text"] = f"Saved {save_path}"

    def get_frame(self):
        if not self.cap.isOpened():
            logging.error("Camera not opened")
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            logging.warning("Failed to capture frame.")
            return False, None

        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.ascontiguousarray(frame_rgb, dtype=np.uint8)

        return True, frame_rgb


    def process(self):
        ret, self.current_frame = self.get_frame()

        if not ret or self.current_frame is None:
            logging.warning("Skipping frame processing due to invalid frame.")
            self.win.after(20, self.process)
            return

        # Ensure frame is proper RGB
        try:
            rgb_frame = np.ascontiguousarray(self.current_frame, dtype=np.uint8)
            if rgb_frame.ndim != 3 or rgb_frame.shape[2] != 3:
                raise ValueError("Frame is not 3-channel RGB.")

            faces = detector(rgb_frame, 1)
            logging.debug(f"Dlib detected {len(faces)} faces.")
        except Exception as e:
            logging.error(f"Dlib detector error: {e}")
            self.label_warning["text"] = f"Dlib error: {e}"
            self.win.after(20, self.process)
            return  # 🔁 Prevent NameError

        self.current_frame_faces_cnt = len(faces)
        self.label_face_cnt["text"] = str(len(faces))
        display_frame = self.current_frame.copy()

        if len(faces) == 1:
            face = faces[0]
            self.face_ROI_width_start = face.left()
            self.face_ROI_height_start = face.top()
            self.face_ROI_height = face.bottom() - face.top()
            self.face_ROI_width = face.right() - face.left()
            self.hh = int(self.face_ROI_height / 2)
            self.ww = int(self.face_ROI_width / 2)

            # Check if the crop box goes out of frame boundaries (640x480)
            if (self.face_ROI_width_start - self.ww < 0 or
                self.face_ROI_height_start - self.hh < 0 or
                self.face_ROI_width_start + self.face_ROI_width + self.ww > 640 or
                self.face_ROI_height_start + self.face_ROI_height + self.hh > 480):
                self.out_of_range_flag = True
                self.label_warning["text"] = "OUT OF RANGE"
                self.label_warning["fg"] = "red"
            else:
                self.out_of_range_flag = False
                self.label_warning["text"] = ""
        else:
            self.out_of_range_flag = False
            self.label_warning["text"] = ""

        for face in faces:
            x1 = max(0, face.left())
            y1 = max(0, face.top())
            x2 = min(display_frame.shape[1], face.right())
            y2 = min(display_frame.shape[0], face.bottom())
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        self.update_fps()

        img_Image = Image.fromarray(display_frame)
        img_PhotoImage = ImageTk.PhotoImage(image=img_Image)
        self.label.img_tk = img_PhotoImage
        self.label.configure(image=img_PhotoImage)

        self.win.after(20, self.process)


    def run(self):
        self.pre_work_mkdir()
        self.check_existing_faces_cnt()
        self.GUI_info()
        self.process()
        self.win.mainloop()
        if self.cap.isOpened():
            self.cap.release()


def main():
    app = Face_Register()
    if app.win.winfo_exists():
        app.run()


if __name__ == '__main__':
    main()
