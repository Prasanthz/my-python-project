import os
import cv2
import glob
import numpy as np
import face_recognition

ENCODINGS_FILE = "face_encodings.npy"

class simplefacerec:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.frame_resizing = 0.25

        # Load existing encodings if available
        self.load_stored_encodings()

    def load_encoding_images(self, images_path):
        """Encodes images and creates authorized_users.txt if missing."""
        
        # Clear old data
        self.known_face_encodings = []
        self.known_face_names = []

        images_path = glob.glob(os.path.join(images_path, "*.jpg")) + \
                    glob.glob(os.path.join(images_path, "*.png")) + \
                    glob.glob(os.path.join(images_path, "*.jpeg"))

        print(f"Found {len(images_path)} images for encoding.")

        new_users = []  # Collect new names

        for image_path in images_path:
            img = cv2.imread(image_path)
            if img is None:
                print(f"Error loading image: {image_path}")
                continue

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            basename = os.path.basename(image_path)
            filename, _ = os.path.splitext(basename)

            try:
                img_encoding = face_recognition.face_encodings(rgb_img)
                if img_encoding:
                    self.known_face_encodings.append(img_encoding[0])
                    self.known_face_names.append(filename)
                    new_users.append(filename)
                    print(f"Encoded: {filename}")
                else:
                    print(f"No face found in {filename}")

            except Exception as e:
                print(f"Error encoding {filename}: {e}")

        self.save_encodings()

        with open("authorized_users.txt", "w") as file:
            for user in new_users:
                file.write(f"{user}\n")

        print("Encodings saved successfully. Authorized users list updated.")

    def save_encodings(self):
        """Saves face encodings and names to a file."""
        np.save(ENCODINGS_FILE, {"encodings": self.known_face_encodings, "names": self.known_face_names})
        print("Encodings saved successfully.")

    def load_stored_encodings(self):
        """Loads stored face encodings if available."""
        if os.path.exists(ENCODINGS_FILE):
            data = np.load(ENCODINGS_FILE, allow_pickle=True).item()
            self.known_face_encodings = data["encodings"]
            self.known_face_names = data["names"]
            print(f"Loaded {len(self.known_face_names)} stored encodings.")

    def detect_known_faces(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            tolerance = 0.4  # Stricter match (default is 0.6)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance)
            name = "Unknown"

            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
            face_names.append(name)

        face_locations = np.array(face_locations) / self.frame_resizing
        return face_locations.astype(int), face_names
