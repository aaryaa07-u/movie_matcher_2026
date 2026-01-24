from flask import Flask, flash, render_template, request, redirect, url_for, session
from user import User

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
def dashboard():
    if 'user_email' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    user = User.get_user(session['user_email'])
    return render_template("dashboard.html", user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)