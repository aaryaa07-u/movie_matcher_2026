from flask import Flask, flash, render_template, request, redirect, url_for, session
from user import User
from review import Review
from movies import Movies
from auth import login_required
from functools import lru_cache

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Cache for expensive operations
_movies_cache = None
_genres_cache = None
_cache_version = 0

def get_cached_movies():
    """Get movies with caching."""
    global _movies_cache, _cache_version
    if _movies_cache is None:
        print("Loading movies from disk...")
        _movies_cache = Movies.load_movies()
        _cache_version += 1
    return _movies_cache

def get_cached_genres():
    """Get genres with caching."""
    global _genres_cache
    if _genres_cache is None:
        print("Loading genres...")
        _genres_cache = Movies.get_genres()
    return _genres_cache

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    email = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        success, message = User.create_user(email, password, confirm_password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))

        else:
            flash(message, 'error')

    return render_template("register.html", email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, message = User.authenticate_user(email, password)
        
        if success:
            session['user_email'] = email
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
    
    return render_template("login.html")

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.get_user(session['user_email'])
    genres = get_cached_genres()
    return render_template("dashboard.html", user=user, genres=genres)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/reviews', methods=['GET', 'POST'])
@login_required
def reviews():
    if request.method == 'POST':
        movie_id = request.form.get('movieId')
        recommendation_score = int(request.form.get('recommend'))
        acting_score = int(request.form.get('acting'))
        quality_score = int(request.form.get('quality'))
        rewatch_score = int(request.form.get('rewatch'))
        engagement = int(request.form.get('engagement'))
        written_review = request.form.get('reviewText')

        success, message = Review.save_review(
            user_email=session['user_email'],
            movie_id=movie_id,
            recommendation_score=recommendation_score,
            acting_score=acting_score,
            quality_score=quality_score,
            rewatch_score=rewatch_score,
            engagement=engagement,
            written_review=written_review
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('search'))
        else:
            flash(message, 'error')
    return redirect(url_for('dashboard'))                   

 

@app.route('/search')
@login_required
def search():
    # Get all search parameters
    title = request.args.get('title', '').lower()
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    cast = request.args.get('cast', '').lower()
    rating = request.args.get('rating', '')
    
    print(f"Search filters - Title: {title}, Genre: {genre}, Year: {year}, Cast: {cast}, Rating: {rating}")
    
    # Use cached movies instead of loading from disk
    movies = get_cached_movies()
    genres = get_cached_genres()
    results = []
    
    # Limit results to 500 for performance
    MAX_RESULTS = 500
    
    # Filter movies based on all parameters
    for movie_id, movie in movies.items():
        try:
            # Title filter
            if title and title not in movie.get('title', '').lower():
                continue
            
            # Genre filter
            if genre and genre not in movie.get('genres', []):
                continue
            
            # Year filter
            if year:
                try:
                    year_int = int(year)
                    movie_year = movie.get('year')
                    if movie_year != year_int:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Rating filter (minimum rating)
            if rating:
                try:
                    rating_float = float(rating)
                    movie_rating = movie.get('rating')
                    if movie_rating is None or movie_rating < rating_float:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Cast filter (if available)
            if cast and 'cast' in movie:
                if cast not in movie.get('cast', '').lower():
                    continue
            
            # Movie passed all filters
            results.append(movie)
        except Exception as e:
            print(f"Error filtering movie {movie_id}: {e}")
            continue
    
    # Sort results by weighted rating (rating adjusted by vote count)
    # This prevents high-rated movies with few votes from ranking above well-voted movies
    def weighted_rating(m):
        rating = m.get('rating') or 0 
        votes = m.get('votes') or 0
        # Weighted formula: higher votes increase confidence in the rating
        # Uses (votes / votes + 5000) * rating to balance rating and vote count
        return (votes / (votes + 5000)) * rating
    
    results.sort(key=weighted_rating, reverse=True)
    
    # Limit to top MAX_RESULTS after sorting
    results = results[:MAX_RESULTS]
    
    result_count = len(results)
    if result_count == MAX_RESULTS:
        print(f"Showing top {MAX_RESULTS} results by rating. Refine your search to see different results.")
    
    return render_template("search.html", 
                         title=title, 
                         genre=genre, 
                         year=year, 
                         cast=cast, 
                         rating=rating,
                         results=results, 
                         genres=genres,
                         result_count=result_count)

if __name__ == "__main__":
    app.run(debug=True)