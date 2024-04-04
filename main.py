# import cProfile uncomment when needed

# Kivy imports
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import TwoLineListItem
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.utils import platform
from kivy.resources import resource_find
# Conditional import for Android-specific functionality
if platform == 'android':
    from android.permissions import request_permissions, Permission
    # Define any Android-specific functionality here
else:
    # Mock or no-op versions of Android-specific functionality for non-Android platforms
    def request_permissions(*args, **kwargs):
        pass  # No operation if not on Android


# General Python imports
import numpy as np
import datetime
import requests
import json 
from firebase_admin import db
from PIL import Image


# Custom imports
from red_recognition import RedRecognition
from user import User, UserManager
from test_result_detail import TestResultDetail


def read_text_file(file_path):
    full_path = resource_find(file_path)
    if full_path:
        with open(full_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return "File not found: " + file_path

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
    instructions_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instructions_text = read_text_file('kv/test_instructions_text.txt')
    pass


class CameraWindow(Screen):
    def on_enter(self, *args):
        super(CameraWindow, self).on_enter(*args)
        # Start the camera
        self.ids.camera.play = True

    def on_leave(self, *args):
        super(CameraWindow, self).on_leave(*args)
        # Stop t he camera
        self.ids.camera.play = False

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
        date = test_entry['date']  

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
        self.root.ids.screen_manager.get_screen('camera_window').on_enter() # type: ignore

    def on_stop(self):
        self.root.ids.screen_manager.get_screen('camera_window').on_leave()  # type: ignore

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
        camera_window = self.root.ids.screen_manager.get_screen('camera_window') #type: ignore
        camera_texture = camera_window.ids.camera.texture
        if camera_texture:
            # Extract image data from the texture
            size = camera_texture.size
            pixels = camera_texture.pixels
            # Convert pixel data to an array
            arr = np.frombuffer(pixels, dtype=np.uint8).reshape(size[1], size[0], 4)
            # Convert from kivy's texture format (RGBA) to standard RGB for PIL
            arr = arr[:, :, :-1]  # Drop the alpha channel
            
            # Create an image using PIL
            img = Image.fromarray(arr)
            image_path = 'test_strip.png'
            img.save(image_path)
            
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



         
