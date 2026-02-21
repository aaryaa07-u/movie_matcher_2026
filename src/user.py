import json
import os
from user_preferences import UserPreferences

class User:
    """User class for authentication and registration management."""
    
    USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
    REVIEWS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
    _user_review_cache = None
    _users_cache = None
    def __init__(self, email, password=None, displayName=None, preferences=None):
        """Initialize a User instance."""
        print("Initializing User instance with email:", email)
        self.__email = email
        self.__password = password
        self.__displayName = displayName
        self.__preferences = UserPreferences.from_dict(preferences)
         
    def get_email(self):
        """Get the user's email.""" 
        return self.__email
    
    def get_displayName(self):
        """Get the user's display preferred name."""
        return self.__displayName

    def get_preferred_genres(self):
        """Get the user's preferred genres."""
        return self.__preferences.get_genres() 
    
    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if not any(c.isdigit() for c in password):
            return False, "Password must include at least one digit."
        if not any(c.isupper() for c in password):
            return False, "Password must include at least one uppercase letter."
        if not any(c.islower() for c in password):
            return False, "Password must include at least one lowercase letter."
        return True, "Password is strong."
    
    @staticmethod
    def load_users():
        if (User._users_cache == None):
            User.load_users_from_disk()
        return User._users_cache
        
        

    @staticmethod
    def load_users_from_disk():   
        """Load all users from the JSON file."""
        if os.path.exists(User.USERS_FILE):
            with open(User.USERS_FILE, 'r') as f:
                User._users_cache = json.load(f)
        return {}
    
    @staticmethod
    def save_users(users_dict):
        """Save users to the JSON file."""
        os.makedirs(os.path.dirname(User.USERS_FILE), exist_ok=True)
        with open(User.USERS_FILE, 'w') as f:
            json.dump(users_dict, f, indent=4)
    
    @staticmethod
    def email_exists(email):
        """Check if an email is already registered."""
        users = User.load_users()
        return email in users
    
    def to_dict(self):
        """Convert the User instance to a dictionary for JSON storage."""
        return {
            self.__email : {
            "password": self.__password,
            "displayName": self.__displayName,
            "preferences": self.__preferences.to_dict()
            }
        }
    
    @staticmethod
    def create_user(email, displayName, password, confirm_password, preferences):
        """Register a new user with validation."""
        # Check if email already exists
        if User.email_exists(email):
            return False, "Email already registered."
        
        # Validate password match
        if password != confirm_password:
            return False, "Passwords do not match."
        
        # Validate password strength
        is_valid, message = User.validate_password(password)
        if not is_valid:
            return False, message
        
        # Hash password and save user
        users = User.load_users()
        hashed_password = User.__encrypt_password(password, email)
        preferences = UserPreferences.set_registeration_rating(preferences)
        new_user = User(email, hashed_password, displayName, preferences)
        # Merge the inner user review(s) 
        for user_email, record in new_user.to_dict().items(): 
            users[email] = record
        User.save_users(users)
        return True, "User registered successfully."
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate a user by email and password."""
        users = User.load_users()
        User._user_review_cache = None
        
        if email not in users:
            return False, "Invalid username/password."
        
        stored_password_hash = users[email]['password']
        print("Stored password hash:", stored_password_hash)
        
        encrypted_password = User.__encrypt_password(password, email)
        print("Encrypted password:", encrypted_password)

        if encrypted_password == stored_password_hash:
            return True, "Login successful."
        else:
            return False, "Invalid username/password."
    
    @staticmethod
    def get_user(email):
        """Get user data by email."""
        users = User.load_users()
        if email in users:
            return User(email, users[email]['password'], users[email]['displayName'], users[email]['preferences'])
    
    def load_user_reviews(self):
        """Load reviews submitted by this user."""
        if User._user_review_cache is None:
            print("Loading user reviews from disk...")
            self.load_reviews_from_disk()
        return User._user_review_cache

    def load_reviews_from_disk(self):
        if os.path.exists(User.REVIEWS_FILE):
            with open(User.REVIEWS_FILE, 'r') as f:
                reviews = json.load(f)
                user_reviews = {}
                for movie_id, movie_reviews in reviews.items():
                    if self.__email in movie_reviews:
                        user_reviews[movie_id] = movie_reviews[self.__email]
                User._user_review_cache = user_reviews



    def delete_movie_review(self, movie_id): 
        User._user_review_cache.pop(movie_id, None)



        
        
    #creating my own hash function
    def __encrypt_password(password: str, email : str) -> str:
            data = (email + password + "moviematcher07").encode("utf-8")
            hash_value = 0

            for byte in data:
                hash_value = (hash_value * 131 + byte) % (2**64)

            return hex(hash_value)[2:]