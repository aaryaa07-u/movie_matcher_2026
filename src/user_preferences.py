class UserPreferences:
    """Class to manage user preferences, including preferred genres."""
    REGISTRATION_GENRE_SCORE = 1.0  # Weight for genre preferences in recommendations
    REVIEW_SCORE = 0.2
    def __init__(self):
        self.genre: dict[str, float] = {}
        self.cast: dict[str, float] ={}
    def to_dict(self):
        """Convert the UserPreferences instance to a dictionary for JSON storage."""
        return {
            "genres": self.genre,
            "cast": self.cast 
        }
    @staticmethod
    def from_dict(data):
        """Create a UserPreferences instance from a dictionary."""
        preferences = UserPreferences()
        preferences.genre = data.get("genres", {})
        preferences.cast = data.get("cast", {})
        return preferences
    @staticmethod
    def set_registeration_rating(data):
        """Create a UserPreferences instance from a dictionary."""
        preference = UserPreferences()
        for genre in data.get('genres'):
            preference.genre[genre] = UserPreferences.REGISTRATION_GENRE_SCORE           
        return preference.to_dict()
    
    def update_preferences(self, data):
        # Update genre preferences
        if "genres" in data:

            for genre in data.get('genres'):
                self.genres[genre] = self.genres.get(genre, 0) + UserPreferences.REVIEW_SCORE

        # Update cast preferences
        if "cast" in data :
            for person in data.get('cast'):
                self.cast[person] = self.cast.get(person, 0) + UserPreferences.REVIEW_SCORE


        return self

    
    def get_genres(self):
        return sorted(self.genre, key=self.genre.get, reverse=True)
    
    def get_cast(self):
        return sorted(self.cast, key= self.cast.get, reverse = True )
    
    
    
    




        
    