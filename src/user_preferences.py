class UserPreferences:
    """Class to manage user preferences, including preferred genres."""
    REGISTRATION_GENRE_SCORE = 1.0  # Weight for genre preferences in recommendations
    def __init__(self):
        self.genre: dict[str, float] = {}
    def to_dict(self):
        """Convert the UserPreferences instance to a dictionary for JSON storage."""
        return {
            "genres": self.genre
        }
    @staticmethod
    def from_dict(data):
        """Create a UserPreferences instance from a dictionary."""
        preferences = UserPreferences()
        preferences.genre = data.get("genres", {})
        return preferences
    @staticmethod
    def set_registeration_rating(data):
        """Create a UserPreferences instance from a dictionary."""
        preference = UserPreferences()
        for genre in data.get('genres'):
            preference.genre[genre] = UserPreferences.REGISTRATION_GENRE_SCORE           
        return preference.to_dict()
    
    def get_genres(self):
        return sorted(self.genre, key=self.genre.get, reverse=True)



        
    