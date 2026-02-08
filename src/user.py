import json
import os
from movies import Movies


class User:
    """User class for authentication and registration management."""
    
    USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
    REVIEWS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
    def __init__(self, email, password=None, display_name=None):
        """Initialize a User instance."""
        print("Initializing User instance with email:", email)
        self.__email = email
        self.__password = password
        self.__display_name = display_name
    

    def get_email(self):
        """Get the user's email.""" 
        return self.__email
    
    def get_display_name(self):
        """Get the user's display name."""
        return self.__display_name

#To display the user's own reviews on the dashboard
    def load_user_reviews(self):

        # Load reviews.json
        if os.path.exists(User.REVIEWS_FILE):
            with open(User.REVIEWS_FILE, 'r') as f:
                my_reviews = json.load(f)
        else:
            return []

        # Load movies
        user_reviews = []

        # Loop through movie IDs in reviews.json
        for movie_id, users in my_reviews.items():
            if self.__email in users:
                my_review = users[self.__email]
                movie = Movies.get_movie_by_id(movie_id)
                user_reviews.append({
                    'movie': movie,
                    'recommendation_score': my_review['recommendation_score'],
                    'acting_score': my_review['acting_score'],
                    'quality_score': my_review['quality_score'],
                    'rewatch_score': my_review['rewatch_score'],
                    'engagement': my_review['engagement'],
                    'written_review': my_review['written_review']
                })
        return user_reviews


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
        """Load all users from the JSON file."""
        if os.path.exists(User.USERS_FILE):
            with open(User.USERS_FILE, 'r') as f:
                return json.load(f)
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
    
    @staticmethod
    def create_user(email, display_name, password, confirm_password):
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

        users[email] = {
            'password': hashed_password,
            'email': email,
            'displayName': display_name
        }
        User.save_users(users)
        return True, "User registered successfully."
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate a user by email and password."""
        users = User.load_users()
        
        if email not in users:
            return False, "Invalid username/password."
        
        stored_password_hash = users[email]['password']
        
        encrypted_password = User.__encrypt_password(password, email)

        if encrypted_password == stored_password_hash:
            return True, "Login successful."
        else:
            return False, "Invalid username/password."
    
    @staticmethod
    def get_user(email):
        """Get user data by email."""
        users = User.load_users()
        if email in users:
            return User(email, users[email]['password'], users[email]['displayName'])
    

    #creating my own hash function
    def __encrypt_password(password: str, email : str) -> str:
            data = (email + password + "moviematcher07").encode("utf-8")
            hash_value = 0

            for byte in data:
                hash_value = (hash_value * 131 + byte) % (2**64)

            return hex(hash_value)[2:]