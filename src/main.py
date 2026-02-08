from flask import Flask, flash, render_template, request, redirect, url_for, session
from user import User
from review import Review
from movies import Movies
from auth import login_required
from functools import lru_cache


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

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
        display_Name = request.form.get('displayName')
        
        success, message = User.create_user(email, display_Name, password, confirm_password)
        
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
    user_email = session['user_email']
    user = User.get_user(user_email)
    genres = Movies.get_cached_genres()

    user_reviews = Movies.get_user_reviews(user)

    return render_template(
        "dashboard.html",
        user=user,
        genres=genres,
        user_reviews=user_reviews
    )


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
        acting_score = int(request.form.get('acting'))
        quality_score = int(request.form.get('quality'))
        rewatch_score = int(request.form.get('rewatch'))
        engagement_score = int(request.form.get('engagement'))
        written_review = request.form.get('reviewText')

        # Save review
        success, message = Review.save_review(
            user_email=session['user_email'],
            movie_id=movie_id,
            recommendation_score=recommendation_score,
            acting_score=acting_score,
            quality_score=quality_score,
            rewatch_score=rewatch_score,
            engagement=engagement_score,
            written_review=written_review,
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('search'))
        else:
            flash(message, 'error')

        

                  

 

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
    movies = Movies.get_cached_movies()
    genres = Movies.get_cached_genres()
    results = []
    
    # Limit results to 500 for performance
    MAX_RESULTS = 50

    
    # Filter movies based on all parameters
    for movie in movies:
        try:
            # Title filter
            if title and title not in movie.title.lower():
                continue
            
            # Genre filter
            if genre and genre not in movie.genres:
                continue
            
            # Year filter
            if year:
                try:
                    year_int = int(year)
                    movie_year = movie.year
                    if movie_year != year_int:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Rating filter (minimum rating)
            if rating:
                try:
                    rating_float = float(rating)
                    movie_rating = movie.rating
                    if movie_rating is None or movie_rating < rating_float:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Cast filter (if available)
            if cast and 'cast' in movie:
                if cast not in movie.cast.lower():
                    continue
            
            # Movie passed all filters
            results.append(movie)
        except Exception as e:
            print(f"Error filtering movie {movie.id}: {e}")
            continue
    
    # Sort results by weighted rating (rating adjusted by vote count)
    # This prevents high-rated movies with few votes from ranking above well-voted movies
    def weighted_rating(m):
        rating = m.rating or 0 
        votes = m.votes or 0
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