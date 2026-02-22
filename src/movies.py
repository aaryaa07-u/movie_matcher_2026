import json
import os
import gzip
import csv
from review import Review
from user import User

class Movies:
    temp_status = None
    """FileDB class for handling file-based database operations."""
    MOVIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'movies.json') 
    RECOMMENDATION_LIMIT = 5
    # Cache for expensive operations
    _movies_cache = None
    _genres_cache = None
    _cache_version = 0

    "-""Initialize the FileDB with the given file path."""
    __data_dir = 'data'
    __imdb_dir = os.path.join(__data_dir, "imdb")
    os.makedirs(__data_dir, exist_ok=True)
    os.makedirs(__imdb_dir, exist_ok=True)   

    def __init__(self, movie_id, title, year, genres, runtime, rating, votes, cast, directors):
        self.id = movie_id
        self.title = title
        self.year = year
        self.genres = genres
        self.runtime = runtime
        self.rating = rating
        self.votes = votes
        self.cast = cast
        self.directors = directors
        


    @staticmethod
    def from_json(movie_id, data):
        all_cast = data.get("cast")
        acting_cast = all_cast["actor"] + all_cast["actress"]
        

        return Movies(
            movie_id=movie_id,
            title=data.get("title"),
            year=data.get("year"),
            genres=data.get("genres"),
            runtime=data.get("runtime"),
            rating=data.get("rating"),
            votes=data.get("votes"),
            cast= acting_cast,
            directors=all_cast["director"]
        )

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "genres": self.genres,
            "runtime": self.runtime,
            "rating": self.rating,
            "votes": self.votes
        }
    
    @staticmethod
    def get_cached_movies():
        """Get movies with caching."""
        if Movies._movies_cache is None:
            print("Loading movies from disk...")
            Movies._movies_cache = Movies.get_all_movies()
            Movies._cache_version += 1
        return Movies._movies_cache
    
    @staticmethod
    def get_cached_genres():
        """Get genres with caching."""
        if Movies._genres_cache is None:
            print("Loading genres...")
            Movies._genres_cache = Movies.get_genres()
        return Movies._genres_cache     

    def _process_imdb_data():
        """Process IMDb data files with ratings, cast, and proper filtering using csv.DictReader."""
        print("Processing IMDb data files...")
        
        # Define file paths
        title_basics_file = os.path.join(Movies.__imdb_dir, "title.basics.tsv.gz")
        title_ratings_file = os.path.join(Movies.__imdb_dir, "title.ratings.tsv.gz")
        name_basics_file = os.path.join(Movies.__imdb_dir, "name.basics.tsv.gz")
        title_principals_file = os.path.join(Movies.__imdb_dir, "title.principals.tsv.gz")
        title_crew_file = os.path.join(Movies.__imdb_dir, "title.crew.tsv.gz")
        
        movies_data = {}
        
        try:
            # Step 1: Read title.ratings.tsv.gz and filter
            print("Step 1: Reading title.ratings.tsv.gz...")
            if not os.path.exists(title_ratings_file):
                print(f"Error: {title_ratings_file} not found")
                return {}
            
            df_ratings = {}
            total_ratings = 0
            
            with gzip.open(title_ratings_file, 'rt', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    total_ratings += 1
                    try:
                        num_votes = int(row['numVotes'])
                        # Only keep ratings with at least 1000 votes
                        if num_votes >= 1000:
                            df_ratings[row['tconst']] = {
                                'averageRating': float(row['averageRating']),
                                'numVotes': num_votes
                            }
                    except (ValueError, KeyError):
                        continue
            
            print(f"  Total ratings: {total_ratings}")
            print(f"  After numVotes>=1000 filter: {len(df_ratings)}")
            
            # Create set of movie IDs with good ratings for faster lookup
            rated_movie_ids = set(df_ratings.keys())
            
            # Step 2: Read title.basics.tsv.gz
            print("Step 2: Reading title.basics.tsv.gz...")
            if not os.path.exists(title_basics_file):
                print(f"Error: {title_basics_file} not found")
                return {}
            
            df_movies = {}
            total_titles = 0
            
            with gzip.open(title_basics_file, 'rt', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    total_titles += 1
                    
                    try:
                        movie_id = row['tconst']
                        
                        # Skip if not a movie
                        if row['titleType'] != 'movie':
                            continue
                        
                        # Skip adult content
                        if row['isAdult'] == '1':
                            continue
                        
                        # Skip if no year
                        if row['startYear'] == '\\N':
                            continue
                        
                        # Skip if doesn't have ratings
                        if movie_id not in rated_movie_ids:
                            continue
                        
                        try:
                            year = int(row['startYear'])
                            runtime = int(row['runtimeMinutes']) if row['runtimeMinutes'] != '\\N' else None
                        except (ValueError, KeyError):
                            continue
                        
                        genres = row['genres'].split(',') if row['genres'] != '\\N' else []
                        
                        df_movies[movie_id] = {
                            'primaryTitle': row['primaryTitle'],
                            'startYear': year,
                            'runtimeMinutes': runtime,
                            'genres': genres
                        }
                    except KeyError:
                        continue
            
            print(f"  Total titles: {total_titles}")
            print(f"  Qualified movies: {len(df_movies)}")
            
            if not df_movies:
                print("No movies found matching criteria")
                return {}
            
            # Step 3: Read name.basics.tsv.gz
            print("Step 3: Reading name.basics.tsv.gz...")
            if not os.path.exists(name_basics_file):
                print(f"Error: {name_basics_file} not found")
                names_lookup = {}
            else:
                names_lookup = {}
                total_names = 0
                
                with gzip.open(name_basics_file, 'rt', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for row in reader:
                        total_names += 1
                        try:
                            names_lookup[row['nconst']] = row['primaryName']
                        except KeyError:
                            continue
                
                print(f"  Total names: {total_names}")
                print(f"  Loaded {len(names_lookup)} names")
            
            # Step 4: Read title.principals.tsv.gz and build cast data
            print("Step 4: Reading title.principals.tsv.gz...")
            if not os.path.exists(title_principals_file):
                print(f"Error: {title_principals_file} not found")
                cast_data = {}
            else:
                cast_data = {}
                total_principals = 0
                chunk_count = 0
                
                with gzip.open(title_principals_file, 'rt', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for row in reader:
                        total_principals += 1
                        chunk_count += 1
                        
                        try:
                            movie_id = row['tconst']
                            category = row['category']
                            person_id = row['nconst']
                            
                            # Skip if movie not in our list
                            if movie_id not in df_movies:
                                continue
                            
                            # Only include actor, actress, and director
                            if category not in ['actor', 'actress', 'director']:
                                continue
                            
                            # Skip if person not found
                            if person_id not in names_lookup:
                                continue
                            
                            person_name = names_lookup[person_id]
                            
                            # Initialize cast data for this movie
                            if movie_id not in cast_data:
                                cast_data[movie_id] = {
                                    'actor': [],
                                    'actress': [],
                                    'director': []
                                }
                            
                            # Add person to their category (avoid duplicates)
                            if person_name not in cast_data[movie_id][category]:
                                cast_data[movie_id][category].append(person_name)
                        except KeyError:
                            continue
                        
                        if chunk_count % 100000 == 0:
                            print(f"  Processed {total_principals} principals, {len(cast_data)} movies with cast")
                
                print(f"  Total principals: {total_principals}")
                print(f"  Movies with cast info: {len(cast_data)}")
            
            # Step 5: Create movie objects
            print("Step 5: Creating movie objects...")
            for movie_id, movie_info in df_movies.items():
                try:
                    # Get cast data if available
                    cast_info = cast_data.get(movie_id, {
                        'actor': [],
                        'actress': [],
                        'director': []
                    })
                    
                    # Get rating data
                    rating_info = df_ratings[movie_id]
                    
                    movies_data[movie_id] = {
                        'id': movie_id,
                        'title': movie_info['primaryTitle'],
                        'year': movie_info['startYear'],
                        'runtime': movie_info['runtimeMinutes'],
                        'genres': movie_info['genres'],
                        'rating': rating_info['averageRating'],
                        'votes': rating_info['numVotes'],
                        'cast': cast_info
                    }
                except Exception as e:
                    print(f"Warning: Error processing movie {movie_id}: {e}")
                    continue
            
            # Step 6: Save to JSON
            print(f"Step 6: Saving {len(movies_data)} movies to JSON...")
            Movies.save_movies(movies_data)
            print(f"✓ Successfully processed {len(movies_data)} movies")
            return movies_data
            
        except Exception as e:
            print(f"Error processing IMDb data: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @staticmethod
    def save_movies(movies_dict):
        """Save movies to the JSON file."""
        os.makedirs(os.path.dirname(Movies.MOVIES_FILE), exist_ok=True)
        with open(Movies.MOVIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(movies_dict, f, indent=4, ensure_ascii=False)

    
    @staticmethod
    def get_genres():
        """Extract and return all unique genres from movies."""
        movies = Movies.get_cached_movies()
        genres_set = set()
        
        for movie in movies:
            if movie.genres:
                genres = movie.genres
                if isinstance(genres, list):
                    genres_set.update(genres)
        
        return sorted(list(genres_set))
    
    @staticmethod
    def search_movies_by_genre(genre):
        """Get movies that belong to a specific genre."""
        movies = Movies.get_cached_movies()
        genre_movies = []
        
        for movie in movies:
            if movie.genres and genre in movie.genres:
                genre_movies.append(movie)
        
        return genre_movies
    
    @staticmethod
    def search_movies_by_cast(cast):
        """Get movies that belong to a specific genre."""
        movies = Movies.get_cached_movies()
        result = []
        
        for movie in movies:
            if movie.cast and cast in movie.cast:
                result.append(movie)
        
        return result
    
    @staticmethod
    def get_all_movies():
        # Check if the movies JSON file exists
        if os.path.exists(Movies.MOVIES_FILE):

            # Open the JSON file and load its contents into memory
            with open(Movies.MOVIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            movies = []

            # Convert each JSON entry into a Movie object
            for movie_id, movie_data in data.items():
                movies.append(Movies.from_json(movie_id, movie_data))

            # Return the full list of Movie objects
            return movies

        # If the file does not exist, return an empty list
        return []
    
    @staticmethod
    def get_movie_by_id(movie_id):
        """Get a movie by its ID."""
        movies = Movies.get_cached_movies()
        for movie in movies:
            if movie.id == movie_id:
                return movie
        return None
        
    
    def get_reviews(self):
            """Get reviews for this movie."""
            movie_reviews = Review.get_reviews_for_movie(self.id)
            reviews = []

            for user_email, review in movie_reviews.items():
                user = User.get_user(user_email);
                if user is not None:
                    preferred_name = User.get_user(user_email).get_displayName()
                    review["user_displayName"] = preferred_name
                    reviews.append(review)

            return reviews
    
    def get_recomendations(user):
        recommendations = []
        for genre in user.get_preferred_genres() :
            movies = Movies.search_movies_by_genre(genre)
            sorted_movies = sorted(movies, key=lambda m: m.rating, reverse=True)
            recommendations.extend(sorted_movies[:Movies.RECOMMENDATION_LIMIT])
        return recommendations
        
    def get_user_review(self, user):
        user_reviews = Review.load_user_reviews(user)
        if (user_reviews != None) :
            return user_reviews.get(self.id)
        return None
    
    def delete_user_review(self, user):
        user_reviews = Review.load_user_reviews(user)
        if (user_reviews != None) :
            user_reviews.pop(self.id, None)
        print(user_reviews)
 
    #To display the user's own reviews on the dashboard
    @staticmethod
    def get_user_reviews(user):

        # Load reviews.json
        user_reviews = Review.load_user_reviews(user)
        print("usrReviews")
        print(user_reviews)
        # Load movies
        reviews = []

        # Loop through movie IDs in reviews.json
        for movie_id, review in user_reviews.items():
            movie = Movies.get_movie_by_id(movie_id)
            reviews.append({
                'movie': movie,
                'recommendation_score': review['recommendation_score'],
                'acting_score': review['acting_score'],
                'quality_score': review['quality_score'],
                'rewatch_score': review['rewatch_score'],
                'engagement': review['engagement'],
                'rating': review['rating'],
                    'written_review': review['written_review']
                })
        return reviews
 
    
    

