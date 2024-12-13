from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use environment variable for security

# MySQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sayan1234',
    'database': 'mslogin',
    'port': 3306  # Default MySQL port
}
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    print("Tables:", cursor.fetchall())
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")

# File upload configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/music')
COVER_ART_FOLDER = os.environ.get('COVER_ART_FOLDER', 'uploads/cover_art')
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COVER_ART_FOLDER'] = COVER_ART_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COVER_ART_FOLDER, exist_ok=True)

# Helper function for file validation
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Database Helper Functions
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

music_data = [
    {"title": "Song Title 1", "artist": "Artist 1", "album": "Album 1", "genre": "Pop", "cover": "song-cover1.jpg"},
    {"title": "Song Title 2", "artist": "Artist 2", "album": "Album 2", "genre": "Rock", "cover": "song-cover2.jpg"},
    {"title": "Song Title 3", "artist": "Artist 3", "album": "Album 3", "genre": "Jazz", "cover": "song-cover1.jpg"},
    {"title": "Song Title 4", "artist": "Artist 4", "album": "Album 4", "genre": "Classical", "cover": "song-cover2.jpg"}
]
# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check for existing user
        cursor.execute("SELECT * FROM User WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Username or email already exists!", "error")
            conn.close()
            return redirect(url_for('signup'))

        # Insert new user
        cursor.execute("INSERT INTO User (username, email, password_hash) VALUES (%s, %s, %s)",
                       (username, email, password_hash))
        conn.commit()
        conn.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login_page.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for('login'))

    return render_template('login_page.html')

@app.route('/about.html')
def about():
    return render_template('about.html')
@app.route('/thank_you.html')
def thank_you():
    return render_template('thank_you.html')

@app.route('/audition.html', methods=['GET', 'POST'])
def audition_booking():
    if request.method == 'POST':
        # Extracting form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        audition_date = datetime.strptime(request.form['audition_date'], '%Y-%m-%d').date()
        message = request.form.get('message', '')

        # Insert data into database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audition (name, email, phone, audition_date, message) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, audition_date, message)
        )
        conn.commit()
        conn.close()

        # Flash message for success
        flash("Audition booking successful!", "success")

        # Redirect to prevent form resubmission on page refresh
        return redirect(url_for('thank_you'))

    return render_template('audition.html')



@app.route('/upload', methods=['GET', 'POST'])
def upload_music():
    if request.method == 'POST':
        song_title = request.form['song-title']
        artist_name = request.form['artist-name']
        genre = request.form['genre']
        audio_file = request.files['audio-file']
        cover_art = request.files.get('cover-art')

        if audio_file and allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
            audio_filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            audio_file.save(audio_path)
        else:
            flash("Invalid audio file format.", "error")
            return redirect(url_for('upload_music'))

        cover_art_path = None
        if cover_art and allowed_file(cover_art.filename, ALLOWED_IMAGE_EXTENSIONS):
            cover_filename = secure_filename(cover_art.filename)
            cover_art_path = os.path.join(app.config['COVER_ART_FOLDER'], cover_filename)
            cover_art.save(cover_art_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Upload (song_title, artist_name, genre, file_path, cover_art_path) VALUES (%s, %s, %s, %s, %s)",
            (song_title, artist_name, genre, audio_path, cover_art_path)
        )
        conn.commit()
        conn.close()

        flash("Music uploaded successfully!", "success")
        return redirect(url_for('thank_you'))

    return render_template('upload.html')

@app.route('/show.html', methods=['GET', 'POST'])
def book_show():
    if request.method == 'POST':
        show_name = request.form['show-name']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        tickets = int(request.form['tickets'])
        show_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        message = request.form.get('message', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO show_booking (show_name, name, email, phone, tickets, show_date, message) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (show_name, name, email, phone, tickets, show_date, message)
        )
        conn.commit()
        conn.close()

        flash("Show booked successfully!", "success")
        return redirect(url_for('thank_you'))

    return render_template('show.html')

if __name__ == '__main__':
    app.run(debug=True)
