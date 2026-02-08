import json
import os

class Review:
    REVIEWS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews.json')
    
    
       

    @staticmethod
    def save_review(user_email, movie_id, recommendation_score, acting_score,
                    quality_score, rewatch_score, engagement, written_review):
        """Save a review with basic validation and write to JSON."""

        review_data = {
            "recommendation_score": recommendation_score,
            "acting_score": acting_score,
            "quality_score": quality_score,
            "rewatch_score": rewatch_score,
            "engagement": engagement,
            "written_review": written_review
        }
        
        # Ensure file exists
        reviews_file = "data/reviews.json"
        if not os.path.exists(reviews_file):
            with open(reviews_file, "w") as f:
                json.dump({}, f, indent=4)

        # Load existing reviews
        with open(reviews_file, "r") as f:
            reviews = json.load(f)

        if movie_id not in reviews:
            reviews[movie_id] = {}

        if user_email in reviews[movie_id]:
            return False, "You have already submitted a review for this movie."
        # Check for existing review by the same user for the same movie

        reviews[movie_id][user_email] = review_data


        # Save back to file
        with open(reviews_file, "w") as f:
            json.dump(reviews, f, indent=4)

        return True, "Review submitted successfully."
