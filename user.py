import firebase_admin
from firebase_admin import auth, credentials, exceptions, initialize_app
from firebase_admin import db
import requests


cred = credentials.Certificate('firebase/perio-dx-firebase-credentials.json')

# Initialize the app with your credentials and database URL
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://perio-dx-default-rtdb.firebaseio.com'
})

class UserManager:
    @staticmethod
    def create_user(email, password, first_name, last_name):
        try:
            # Create the user with email and password
            user_record = auth.create_user(
                email=email,
                password=password
            )
            
            # If necessary, save additional user details in the Realtime Database
            # Assuming you have a method to save the data (omitted for brevity)
            additional_user_details = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email
            }
            UserManager.save_user_details(user_record.uid, additional_user_details)
            
            # Return some kind of success message or user data
            return user_record.uid  # For example, return the Firebase Auth user ID

        except exceptions.FirebaseError as e:
            # Handle any Firebase errors that occur during account creation
            print('Failed to create user:', e)
            return None
        
    @staticmethod
    def save_user_details(user_id, user_details):
        # Access the patients reference from the database
        users_ref = db.reference('patients')

        # Create a child node with the user's UID and set the additional details
        users_ref.child(user_id).set(user_details)



class User:
    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        # You might want to consider a more secure way to handle passwords


