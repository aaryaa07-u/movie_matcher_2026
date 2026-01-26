import json
import os
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    """User class for authentication and registration management."""
    
    USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
    
    def __init__(self, email, password=None):
        """Initialize a User instance."""
        self.email = email
        self.password = password
        self.id = None
    
    @staticmethod
    def password_check(password):
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
    def create_user(email, password, confirm_password):
        """Register a new user with validation."""
        # Check if email already exists
        if User.email_exists(email):
            return False, "Email already registered."
        
        # Validate password match
        if password != confirm_password:
            return False, "Passwords do not match."
        
        # Validate password strength
        is_valid, message = User.password_check(password)
        if not is_valid:
            return False, message
        
        # Hash password and save user
        users = User.load_users()
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users[email] = {
            'password': hashed_password,
            'email': email
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
        
        if check_password_hash(stored_password_hash, password):
            return True, "Login successful."
        else:
            return False, "Invalid username/password."
    
    @staticmethod
    def get_user(email):
        """Get user data by email."""
        users = User.load_users()
        if email in users:
            return users[email]
        return None
