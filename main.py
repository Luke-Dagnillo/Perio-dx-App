import cProfile

# Kivy imports
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivymd.uix.button import MDFlatButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivymd.uix.list import TwoLineListItem
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.utils import platform
# Conditional import for Android-specific functionality
if platform == 'android':
    from android.permissions import request_permissions, Permission
    # Define any Android-specific functionality here
else:
    # Mock or no-op versions of Android-specific functionality for non-Android platforms
    def request_permissions(*args, **kwargs):
        pass  # No operation if not on Android


# General Python imports
import cv2
import numpy as np
import datetime
import requests
import json 
from firebase_admin import db

# Custom imports
from red_recognition import RedRecognition
from user import User, UserManager
from test_result_detail import TestResultDetail


# login window
class LoginWindow(Screen):
    def on_pre_leave(self, *args):
        # Clear the text fields when leaving the screen
        self.ids.email.text = ''
        self.ids.password.text = ''
    
# create account window
class CreateAccountWindow(Screen):
    def on_pre_leave(self, *args):
        # Clear the text fields when leaving the screen
        self.ids.first_name.text = ''
        self.ids.last_name.text = ''
        self.ids.email.text = ''
        self.ids.password.text = ''
        self.ids.password_verification.text = ''

# main menu window
class MainMenuWindow(Screen):
    pass

#create test instructions window
class TestInstructionsWindow(Screen):
    pass

class CameraWindow(Screen):
    def start_camera(self):
        # Start capturing video from the camera
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # Update at 30 FPS

    def stop_camera(self):
        Clock.unschedule(self.update)
        self.capture.release()

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            # Flip the frame vertically
            flipped_frame = cv2.flip(frame, 0)
            # Ensure it's a NumPy array
            buf = np.array(flipped_frame)
            # Convert it to texture
            buf_string = buf.tostring()  # type: ignore
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf_string, colorfmt='bgr', bufferfmt='ubyte')
            self.ids.img.texture = texture

#create test history  window
class TestHistoryWindow(Screen):
    def on_test_result_tap(self, antigen, result, date):
        # This function should be bound to an on_release event of the test result widget
        detail_view = TestResultDetail(antigen, result, date)
        detail_view.open()
        
    def show_test_detail(self, test_entry):
        # Assuming test_entry is a dictionary with all the info you need
        antigen = test_entry['antigen']
        result = test_entry['result']
        date = test_entry['date']  # You might need to format this as per your requirements

        # Now, create an instance of TestResultDetail and pass the data
        detail_view = TestResultDetail(antigen=antigen, result=result, date=date)

        # Open the modal view
        detail_view.open()



class MainApp(MDApp):
    my_id = "patients"

    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.user_id = None

    def build(self):
        # Load the main KV file or define your root widget here
        return Builder.load_file('main.kv')  # Assuming 'main.kv' contains the ScreenManager
    
    def on_start(self):
        # Check if running on Android before requesting permissions
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        super().on_start()
        # Proceed with other initialization
        self.root.ids.screen_manager.get_screen('camera_window').start_camera() # type: ignore

    def on_stop(self):
        self.root.ids.screen_manager.get_screen('camera_window').stop_camera()  # type: ignore

    def change_screen(self, screen_name):
        screen_manager = self.root.ids.screen_manager  # type: ignore
        screen_manager.current = screen_name

    def show_dialog(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            size_hint=(0.8, 1),
            buttons=[
                MDFlatButton(
                    text='OK',
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def capture_image(self):
        camera_window = self.root.ids.screen_manager.get_screen('camera_window')  # type: ignore
        ret, frame = camera_window.capture.read()

        image_path = 'test_strip.png'

        if ret:
            # Save the frame as an image file
            cv2.imwrite('test_strip.png', frame)
        
            # Now run the red recognition algorithm on this image
            red_recognizer = RedRecognition(image_path)
            result = red_recognizer.run()

            if result is not None:
                antigen, concentration_level = result
                self.show_dialog("Results", f"{concentration_level} Level of Biomarker Detected")
                user_test_data = self.format_test_data(antigen, concentration_level)

                self.upload_test_result(user_test_data)
            else:
                self.show_dialog("Results", "Try Again")

    def format_test_data(self, antigen_tested, concentration_result):
        # Current date and time
        current_datetime = datetime.datetime.now()

        test_data = {
            'antigen': antigen_tested,
            'result': concentration_result,
            'date': current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        }

        return test_data

    def upload_test_result(self, test_data):
        if self.user_id is not None:
            # Reference to the user's test results in the database
            ref = db.reference(f'/patients/{self.user_id}/test_results')

            # Push new test result
            ref.push().set(test_data)
        else:
            print("User not logged in or user ID not available")

    def toggle_password_visibility(self, text_field, icon_button):
        text_field.password = not text_field.password
        icon_button.icon = "eye" if text_field.password else "eye-off"

    def create_account(self):
        # Access the 'create_account' Screen from the ScreenManager
        create_account_screen = self.root.ids.create_account  # type: ignore

        # Now access the MDTextField using the ids of the 'create_account' Screen
        first_name = create_account_screen.ids.first_name.text
        last_name = create_account_screen.ids.last_name.text
        email = create_account_screen.ids.email.text
        password = create_account_screen.ids.password.text
        password_verify = create_account_screen.ids.password_verification.text

        if password != password_verify:
            self.show_dialog("Error", "Passwords do not match.")
            return

        try:
            user_id = UserManager.create_user(email, password, first_name, last_name)
            if user_id:
                # Account creation successful
                self.show_dialog("Success", "Account created successfully.")
                # Further logic (e.g., redirect to login screen)
                self.change_screen("main_menu")
            else:
                # Handle other potential failures
                self.show_dialog("Error", "Failed to create account.")
        except Exception as e:  # Catch general exception and parse the error
            # Parse the error message to determine the cause
            if 'EMAIL_EXISTS' in str(e):
                self.show_dialog("Error", "An account with this email already exists.")
            else:
                # General error handling
                self.show_dialog("Error", str(e))

    def login_user(self, email, password):
        # You need to obtain this API key from your Firebase project settings
        api_key = 'AIzaSyBlCQcPYU2q0oKiCMVvmEhdr25zCkigjts'

        # The endpoint URL for signing in with email and password
        signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        # The data payload for the POST request
        signin_payload = {
            'email': email,
            'password': password,
            'returnSecureToken': True
        }

        result = requests.post(signin_url, data=json.dumps(signin_payload))
        if result.ok:
            # Login successful
            user_info = result.json()
            # Extract the user ID from the response
            self.user_id = user_info['localId']  # 'localId' typically contains the Firebase user ID
            self.change_screen("main_menu")
        else:
            # Login failed
            self.show_dialog("Error", "Login failed. Please check your credentials.")


    def populate_test_history(self):
        print("populate_test_history called")
        test_history_screen = self.root.ids.screen_manager.get_screen('test_history_window')  # type: ignore
        history_layout = test_history_screen.ids.history_layout

        # Clear existing entries
        history_layout.clear_widgets()

        # Retrieve the test history data for the current user
        test_history_data = self.retrieve_test_history(self.user_id)
        print(f"Retrieved test history data: {test_history_data}")

        for test_entry in test_history_data:
            # Format the date to exclude the exact time, if that's your preference
            date_formatted = datetime.datetime.strptime(test_entry['date'], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
            
            entry_widget = TwoLineListItem(
                text=f"{test_entry['antigen']}",
                secondary_text=f"Result: {test_entry['result']} Concentration | Date: {date_formatted}",
                # Add an on_release event to handle clicks on the list item
                on_release=lambda widget, x=test_entry: self.root.ids.screen_manager.get_screen('test_history_window').show_test_detail(x) # type: ignore
            )

            history_layout.add_widget(entry_widget)

        print(f"Children in history_layout: {history_layout.children}")


    def retrieve_test_history(self, user_id):
        # Make sure you have the correct path to the user's test results
        test_results_ref = db.reference(f'/patients/{user_id}/test_results')

        # Get the data
        test_results = test_results_ref.get()

        # Check if the data exists
        if not test_results:
            return []

        # Convert the data to a list of dictionaries if it's not already in that format
        formatted_results = []
        for test_id, test_data in test_results.items(): # type: ignore
            formatted_results.append({
                'antigen': test_data.get('antigen', 'Unknown'),
                'result': test_data.get('result', 'Unknown'),
                'date': test_data.get('date', 'Unknown')
            })

        # Sort the test results by date in descending order
        formatted_results.sort(key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"), reverse=True)
        return formatted_results






# cProfile.run('MainApp().run()', 'profile_stats') # use for getting profile runtime statistics
            
if __name__ == '__main__':
    MainApp().run()



         
