# # Extract features from images and save into "features_all.csv"

# import os
# import dlib
# import csv
# import numpy as np
# import logging
# import cv2

# #  Path of cropped faces
# path_images_from_camera = "data/data_faces_from_camera/"

# #  Use frontal face detector of Dlib
# detector = dlib.get_frontal_face_detector()

# #  Get face landmarks
# predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

# #  Use Dlib resnet50 model to get 128D face descriptor
# face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")


# #  Return 128D features for single image

# # def return_128d_features(path_img):
# #     img_rd = cv2.imread(path_img)
# #     faces = detector(img_rd, 1)

# #     logging.info("%-40s %-20s", " Image with faces detected:", path_img)

# #     # For photos of faces saved, we need to make sure that we can detect faces from the cropped images
# #     if len(faces) != 0:
# #         shape = predictor(img_rd, faces[0])
# #         face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
# #     else:
# #         face_descriptor = 0
# #         logging.warning("no face")
# #     return face_descriptor

# def return_128d_features(path_img):
#     img_rd = cv2.imread(path_img)

#     if img_rd is None:
#         logging.warning("Failed to load image: %s", path_img)
#         return 0

#     # Ensure it's 8-bit and 3-channel (RGB)
#     if img_rd.dtype != np.uint8:
#         img_rd = img_rd.astype(np.uint8)

#     if len(img_rd.shape) == 2:  # grayscale
#         img_rd = cv2.cvtColor(img_rd, cv2.COLOR_GRAY2RGB)
#     elif img_rd.shape[2] == 3:  # BGR to RGB
#         img_rd = cv2.cvtColor(img_rd, cv2.COLOR_BGR2RGB)
#     else:
#         logging.warning("Invalid image format: %s", path_img)
#         return 0

#     faces = detector(img_rd, 1)

#     logging.info("%-40s %-20s", " Image with faces detected:", path_img)

#     if len(faces) != 0:
#         shape = predictor(img_rd, faces[0])
#         face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
#         return face_descriptor
#     else:
#         logging.warning("No face detected in image: %s", path_img)
#         return 0

# #   Return the mean value of 128D face descriptor for person X

# def return_features_mean_personX(path_face_personX):
#     features_list_personX = []
#     photos_list = os.listdir(path_face_personX)
#     if photos_list:
#         for i in range(len(photos_list)):
#             #  return_128d_features()  128D  / Get 128D features for single image of personX
#             logging.info("%-40s %-20s", " / Reading image:", path_face_personX + "/" + photos_list[i])
#             features_128d = return_128d_features(path_face_personX + "/" + photos_list[i])
#             #  Jump if no face detected from image
#             if features_128d == 0:
#                 i += 1
#             else:
#                 features_list_personX.append(features_128d)
#     else:
#         logging.warning(" Warning: No images in%s/", path_face_personX)

   
#     if features_list_personX:
#         features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
#     else:
#         features_mean_personX = np.zeros(128, dtype=object, order='C')
#     return features_mean_personX


# def main():
#     logging.basicConfig(level=logging.INFO)
#     #  Get the order of latest person
#     person_list = os.listdir("data/data_faces_from_camera/")
#     person_list.sort()

#     with open("data/features_all.csv", "w", newline="") as csvfile:
#         writer = csv.writer(csvfile)
#         for person in person_list:
#             # Get the mean/average features of face/personX, it will be a list with a length of 128D
#             logging.info("%sperson_%s", path_images_from_camera, person)
#             features_mean_personX = return_features_mean_personX(path_images_from_camera + person)

#             if len(person.split('_', 2)) == 2:
#                 # "person_x"
#                 person_name = person
#             else:
#                 # "person_x_tom"
#                 person_name = person.split('_', 2)[-1]
#             features_mean_personX = np.insert(features_mean_personX, 0, person_name, axis=0)
#             # features_mean_personX will be 129D, person name + 128 features
#             writer.writerow(features_mean_personX)
#             logging.info('\n')
#         logging.info("Save all the features of faces registered into: data/features_all.csv")


# if __name__ == '__main__':
#     main()


import os
import dlib
import csv
import numpy as np
import logging
import cv2

# Paths
path_images_from_camera = "data/data_faces_from_camera/"
features_save_path = "data/features_all.csv"

# Dlib models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

def return_128d_features(path_img):
    img_rd = cv2.imread(path_img)

    if img_rd is None:
        logging.warning("Failed to load image: %s", path_img)
        return None

    if img_rd.dtype != np.uint8:
        img_rd = img_rd.astype(np.uint8)

    if len(img_rd.shape) == 2:  # Grayscale
        img_rd = cv2.cvtColor(img_rd, cv2.COLOR_GRAY2RGB)
    elif img_rd.shape[2] == 3:
        img_rd = cv2.cvtColor(img_rd, cv2.COLOR_BGR2RGB)
    else:
        logging.warning("Invalid image format: %s", path_img)
        return None

    faces = detector(img_rd, 1)
    if len(faces) == 0:
        logging.warning("No face detected in image: %s", path_img)
        return None

    shape = predictor(img_rd, faces[0])
    face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
    return np.array(face_descriptor)

def return_features_mean_personX(path_face_personX):
    features_list = []
    photo_list = os.listdir(path_face_personX)

    if not photo_list:
        logging.warning("No images found in: %s", path_face_personX)
        return None

    for photo in photo_list:
        img_path = os.path.join(path_face_personX, photo)
        logging.info("Reading image: %s", img_path)
        features_128d = return_128d_features(img_path)
        if features_128d is not None:
            features_list.append(features_128d)

    if features_list:
        return np.mean(features_list, axis=0)
    else:
        logging.warning("No valid features for: %s", path_face_personX)
        return None

def main():
    logging.basicConfig(level=logging.INFO)

    person_list = sorted(os.listdir(path_images_from_camera))
    with open(features_save_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        for person in person_list:
            person_dir = os.path.join(path_images_from_camera, person)
            logging.info("Processing folder: %s", person_dir)

            features_mean = return_features_mean_personX(person_dir)
            if features_mean is None:
                continue

            if len(person.split('_', 2)) == 2:
                person_name = person
            else:
                person_name = person.split('_', 2)[-1]

            row = [person_name] + list(map(float, features_mean))
            writer.writerow(row)
            logging.info("Saved features for: %s", person_name)

    logging.info("All features saved to: %s", features_save_path)

if __name__ == '__main__':
    main()
