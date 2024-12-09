# with liveliness added and working properly as per the requirements. 
import cv2
import os
import face_recognition
import dlib
import pandas as pd
import json
from tkinter import *
from tkinter import messagebox
from datetime import datetime
from playsound import playsound  # Library to play sounds

# File and Directory Constants
CREDENTIALS_FILE = "class_credentials.json"
STUDENT_IMAGES_PATH = "student_images"
ATTENDANCE_DIR = "attendance_records"
SOUND_FILE = "recognition_sound.mp3"  # Path to the sound file to play
LANDMARKS_MODEL = "shape_predictor_68_face_landmarks.dat"  # Path to dlib landmarks model

# Ensure directories exist
os.makedirs(STUDENT_IMAGES_PATH, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# Load and Save Functions for Class Credentials
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_credentials():
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump(CLASS_CREDENTIALS, file)

# Global Variables
CLASS_CREDENTIALS = load_credentials()

def register_class():
    def submit():
        class_id = class_id_entry.get()
        class_password = class_password_entry.get()
        if class_id and class_password:
            if class_id in CLASS_CREDENTIALS:
                messagebox.showerror("Error", "Class ID already exists!")
            else:
                CLASS_CREDENTIALS[class_id] = class_password
                save_credentials()
                os.makedirs(os.path.join(STUDENT_IMAGES_PATH, class_id), exist_ok=True)
                messagebox.showinfo("Success", "Class Registered!")
                registration_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    registration_window = Toplevel()
    registration_window.title("Register Class")
    registration_window.geometry("400x300")
    Label(registration_window, text="Class ID:").grid(row=0, column=0, padx=10, pady=5)
    class_id_entry = Entry(registration_window)
    class_id_entry.grid(row=0, column=1, padx=10, pady=5)

    Label(registration_window, text="Password:").grid(row=1, column=0, padx=10, pady=5)
    class_password_entry = Entry(registration_window, show="*")
    class_password_entry.grid(row=1, column=1, padx=10, pady=5)

    Button(registration_window, text="Submit", command=submit).grid(row=2, column=0, columnspan=2, pady=10)

def login_faculty():
    def authenticate(selected_class):
        def login():
            entered_password = password_entry.get()
            if CLASS_CREDENTIALS.get(selected_class) == entered_password:
                messagebox.showinfo("Success", "Login Successful!")
                login_window.destroy()
                main_menu(selected_class)
            else:
                messagebox.showerror("Error", "Invalid Credentials.")

        login_window = Toplevel()
        login_window.title(f"Login - {selected_class}")
        login_window.geometry("400x300")
        Label(login_window, text=f"Class ID: {selected_class}").grid(row=0, column=0, columnspan=2, pady=10)
        Label(login_window, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        password_entry = Entry(login_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5)
        Button(login_window, text="Login", command=login).grid(row=2, column=0, columnspan=2, pady=10)

    if not CLASS_CREDENTIALS:
        messagebox.showerror("Error", "No classes registered!")
        return

    selection_window = Toplevel()
    selection_window.title("Select Class")
    selection_window.geometry("400x300")
    Label(selection_window, text="Select a Class to Login:").pack(pady=10)

    for class_id in CLASS_CREDENTIALS.keys():
        Button(selection_window, text=class_id, command=lambda cid=class_id: authenticate(cid)).pack(pady=5)

def register_student(class_id):
    def capture_images():
        student_name = name_entry.get()
        student_id = id_entry.get()
        if not student_name or not student_id:
            messagebox.showerror("Error", "Name and ID cannot be empty!")
            return

        cap = cv2.VideoCapture(0)
        count = 0
        student_path = os.path.join(STUDENT_IMAGES_PATH, class_id, student_id)
        os.makedirs(student_path, exist_ok=True)

        while count < 10:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Capture Images", frame)
            cv2.imwrite(f"{student_path}/{student_name}_{count}.jpg", frame)
            count += 1
            cv2.waitKey(500)

        cap.release()
        cv2.destroyAllWindows()
        messagebox.showinfo("Success", "Images Captured!")

    student_window = Toplevel()
    student_window.title("Register Student")
    student_window.geometry("400x300")
    Label(student_window, text="Student Name:").grid(row=0, column=0, padx=10, pady=5)
    name_entry = Entry(student_window)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    Label(student_window, text="Student ID:").grid(row=1, column=0, padx=10, pady=5)
    id_entry = Entry(student_window)
    id_entry.grid(row=1, column=1, padx=10, pady=5)

    Button(student_window, text="Capture Images", command=capture_images).grid(row=2, column=0, columnspan=2, pady=10)

def take_attendance(class_id):
    known_encodings = []
    known_ids = []

    class_path = os.path.join(STUDENT_IMAGES_PATH, class_id)
    for student_id in os.listdir(class_path):
        student_path = os.path.join(class_path, student_id)
        for image_file in os.listdir(student_path):
            img_path = os.path.join(student_path, image_file)
            img = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                known_encodings.append(encodings[0])
                known_ids.append(student_id)

    cap = cv2.VideoCapture(0)
    present_students = set()
    attendance_data = []

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(LANDMARKS_MODEL)

    def is_blinking(eye_points, facial_landmarks):
        left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
        right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
        center_top = ((facial_landmarks.part(eye_points[1]).x + facial_landmarks.part(eye_points[2]).x) // 2,
                      (facial_landmarks.part(eye_points[1]).y + facial_landmarks.part(eye_points[2]).y) // 2)
        center_bottom = ((facial_landmarks.part(eye_points[5]).x + facial_landmarks.part(eye_points[4]).x) // 2,
                         (facial_landmarks.part(eye_points[5]).y + facial_landmarks.part(eye_points[4]).y) // 2)
        horizontal_length = cv2.norm(left_point, right_point)
        vertical_length = cv2.norm(center_top, center_bottom)
        ratio = vertical_length / horizontal_length
        return ratio > 0.25  # Adjust threshold if necessary

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        faces = face_recognition.face_locations(rgb_frame)
        encodings = face_recognition.face_encodings(rgb_frame, faces)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_dlib = detector(gray_frame)

        for face_encoding, face_location, face_dlib in zip(encodings, faces, faces_dlib):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in matches:
                match_index = matches.index(True)
                student_id = known_ids[match_index]

                if student_id not in present_students:
                    # Check for liveness using blink detection
                    landmarks = predictor(gray_frame, face_dlib)
                    left_eye_blinking = is_blinking([36, 37, 38, 39, 40, 41], landmarks)
                    right_eye_blinking = is_blinking([42, 43, 44, 45, 46, 47], landmarks)

                    if left_eye_blinking or right_eye_blinking:
                        present_students.add(student_id)
                        top, right, bottom, left = [v * 4 for v in face_location]
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, student_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        playsound(SOUND_FILE)  # Play sound on recognition

        cv2.imshow("Attendance", frame)
        if cv2.waitKey(1) == 27:  # Press ESC to stop
            break

    cap.release()
    cv2.destroyAllWindows()

    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    file_date = current_time.strftime("%Y%m%d_%H%M%S")

    for student_id in os.listdir(class_path):
        status = "Present" if student_id in present_students else "Absent"
        attendance_data.append({
            "Student ID": student_id,
            "Status": status,
            "Date & Time": timestamp
        })

    attendance_file = os.path.join(ATTENDANCE_DIR, f"{class_id}_attendance_{file_date}.csv")
    df = pd.DataFrame(attendance_data)
    df.to_csv(attendance_file, index=False)
    messagebox.showinfo("Success", f"Attendance Recorded!\nSaved to: {attendance_file}")

def view_attendance(class_id):
    def display_file(file_name):
        file_path = os.path.join(ATTENDANCE_DIR, file_name)
        if os.path.exists(file_path):
            os.system(f"start {file_path}")
        else:
            messagebox.showerror("Error", "File not found!")

    attendance_files = [f for f in os.listdir(ATTENDANCE_DIR) if f.startswith(class_id) and f.endswith(".csv")]

    if not attendance_files:
        messagebox.showerror("Error", f"No attendance records found for class {class_id}.")
        return

    file_window = Toplevel()
    file_window.title(f"Attendance Records - {class_id}")
    file_window.geometry("400x300")

    Label(file_window, text=f"Attendance Files for Class {class_id}:", font=("Arial", 12, "bold")).pack(pady=10)
    for file_name in attendance_files:
        Button(file_window, text=file_name, command=lambda fn=file_name: display_file(fn)).pack(pady=5)

def main_menu(class_id):
    def logout():
        messagebox.showinfo("Logged Out", f"Successfully logged out from class {class_id}.")
        main_window.destroy()

    main_window = Toplevel()
    main_window.title(f"Main Menu - {class_id}")
    main_window.geometry("400x300")
    Button(main_window, text="Register Student", command=lambda: register_student(class_id)).pack(pady=10)
    Button(main_window, text="Take Attendance", command=lambda: take_attendance(class_id)).pack(pady=10)
    Button(main_window, text="View Attendance", command=lambda: view_attendance(class_id)).pack(pady=10)
    Button(main_window, text="Logout", command=logout).pack(pady=10)

# Main Application Window
root = Tk()
root.title("Facial Recognition Based Attendance System")
root.geometry("600x500")

# Headers
Label(root, text="BANGALORE INSTITUTE OF TECHNOLOGY", font=("Arial", 16, "bold")).pack(pady=10)
Label(root, text="Department of Computer Science and Engineering", font=("Arial", 12, "bold")).pack(pady=10)
Label(root, text="(IoT and Cybersecurity including Blockchain Technology)", font=("Arial", 12, "bold")).pack(pady=5)
Label(root, text="Developed by AHVM", font=("Arial", 8)).pack(side=BOTTOM, pady=10)

# Buttons
Button(root, text="Register Class", command=register_class).pack(pady=10)
Button(root, text="Faculty Login", command=login_faculty).pack(pady=10)

root.mainloop()
