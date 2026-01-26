import json
import os
import gzip
import csv


class Movies:
    """FileDB class for handling file-based database operations."""
    MOVIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'movies.json')

    def __init__(self, data_dir="data"):
        """Initialize the FileDB with the given file path."""
        self.data_dir = data_dir
        self.imdb_dir = os.path.join(self.data_dir, "imdb")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.imdb_dir, exist_ok=True)        

    def _process_imdb_data(self):
        """Process IMDb data files with ratings, cast, and proper filtering using csv.DictReader."""
        print("Processing IMDb data files...")
        
        # Define file paths
        title_basics_file = os.path.join(self.imdb_dir, "title.basics.tsv.gz")
        title_ratings_file = os.path.join(self.imdb_dir, "title.ratings.tsv.gz")
        name_basics_file = os.path.join(self.imdb_dir, "name.basics.tsv.gz")
        title_principals_file = os.path.join(self.imdb_dir, "title.principals.tsv.gz")
        
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
            self.save_movies(movies_data)
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
    def load_movies():
        """Load all movies from the JSON file."""
        if os.path.exists(Movies.MOVIES_FILE):
            with open(Movies.MOVIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def get_genres():
        """Extract and return all unique genres from movies."""
        movies = Movies.load_movies()
        genres_set = set()
        
        for movie_id, movie_data in movies.items():
            if isinstance(movie_data, dict) and 'genres' in movie_data:
                genres = movie_data['genres']
                if isinstance(genres, list):
                    genres_set.update(genres)
        
        return sorted(list(genres_set))
    
    @staticmethod
    def get_all_movies():
        """Get all movies from JSON file."""
        if os.path.exists(Movies.MOVIES_FILE):
            with open(Movies.MOVIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

