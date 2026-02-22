import json
import os
from user import User
class Review:
    REVIEWS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
    _cache = None
    _user_review_cache = None
    @staticmethod
    def save_review(user_email, movie,
        recommendation_score, acting_score,
        quality_score, rewatch_score,
        engagement, written_review):
        """Save a review with validation, scoring, and JSON persistence."""

        # Retrieve the user object for the person submitting the review
        user = User.get_user(user_email)
        movie_id = movie.id

        if acting_score > 4 :
            preferences = user.get_preferences().update_preferences({"cast": movie.cast})
            user.set_preferences(preferences)
            User.save_user(user)

        # Save back to file
        # Build a dictionary containing all review components
        review_data = {
            "recommendation_score": recommendation_score,
            "acting_score": acting_score,
            "quality_score": quality_score,
            "rewatch_score": rewatch_score,
            "engagement": engagement,

            # Calculate an overall rating by averaging the five scores
            "rating": (recommendation_score + acting_score + quality_score + rewatch_score + engagement) / 10,

            # Store the written review text
            "written_review": written_review
        }

        # Load all existing reviews from the JSON cache
        reviews = Review.load_cached_reviews()

        # If this movie has no reviews yet, create an empty entry for it
        if movie_id not in reviews:
            reviews[movie_id] = {}

        # Prevent users from submitting more than one review per movie
        if user_email in reviews[movie_id]:
            return False, "You have already submitted a review for this movie."

        # Save the review under the movie and user
        reviews[movie_id][user_email] = review_data

        # Write the updated review data back to the JSON file
        Review.dump_reviews(reviews)

        # Refresh the user's review list so the dashboard updates immediately
        user.load_reviews_from_disk()

        # Return success status and confirmation message
        return True, "Review submitted successfully."


    
    @staticmethod
    def dump_reviews(reviews):
        # Open the reviews.json file in write mode so the updated
        # reviews dictionary can be saved to persistent storage.
        print("in dumo reviews")
        print(reviews)
        with open(Review.REVIEWS_FILE, "w") as f:
            # Convert the Python dictionary into JSON and write it
            # to the file with indentation for readability.
            json.dump(reviews, f, indent=4)

        # Output the current state of the reviews to the console
        # for debugging and verification during development.

        


    @staticmethod
    def get_reviews_for_movie(movie_id):
        """Get all reviews for a specific movie."""
        reviews = Review.load_cached_reviews()
        movies_reviews = reviews.get(movie_id, {})
        return movies_reviews
    
    @staticmethod
    def load_cached_reviews():
        # If the cache is empty, it means reviews haven't been loaded yet
        if Review._cache is None:
            print("Loading reviews from disk...")   # Debug message to show when disk loading happens

            # Load reviews from the JSON file and store them in the cache
            Review.load_reviews()

        # Return the cached reviews (either freshly loaded or previously stored)
        return Review._cache

    @staticmethod
    def load_user_reviews(user):
        """Load reviews submitted by this user."""
        if Review._user_review_cache is None:
            Review.load_reviews()
            user_reviews = {}

            # Loop through every movie and its associated reviews
            for movie_id, movie_reviews in Review._cache.items():
                # If this user has written a review for the movie, store it
                if user.get_email() in movie_reviews:
                    user_reviews[movie_id] = movie_reviews[user.get_email()]

            # Cache the user's reviews so they can be accessed quickly later
            Review._user_review_cache = user_reviews
        return Review._user_review_cache
    
    @staticmethod
    def load_reviews():
    # Ensure file exists
        print("loading from disk reviews")
        if not os.path.exists(Review.REVIEWS_FILE):
            with open(Review.REVIEWS_FILE, "w") as f:
                json.dump({}, f, indent=4)

        # Load existing reviews
        with open(Review.REVIEWS_FILE, "r") as f:
            Review._cache = json.load(f)

    @staticmethod
    def delete_movie_review(movie_id): 
        Review._user_review_cache.pop(movie_id, None)