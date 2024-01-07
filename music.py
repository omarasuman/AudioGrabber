import os
import uuid
import audiograbber
import boto3
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, flash, session
from models import db, User
from audiograbber import download_music as audiograbber_download_music


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'MYgO9Qu1zU8jo7M5P4EOd0M3JM+C9X885ljBOVg7'

db.init_app(app)

@app.route("/")
@app.route("/home")
# rendering the home page
def home():
    return render_template('home.html')


@app.route("/downloads", methods=["GET", "POST"])
def downloads():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        # Handle the file download form submission
        url = request.form.get("music-url")
        save_dir = "/Users/king-omar/Desktop/AudioGrabber/Music"
        s3_bucket_name = "cloudmediadownloader"

        try:
            # Download music and get file information
            file_info = audiograbber.download_music(url, save_dir, s3_bucket_name)

            # Store file information in the database
            if file_info:
                user_id = session.get('user_id')
                
                source = file_info['source']

               
                db.session.add(new_file)
                db.session.commit()

                # Redirect to the download page after successful download
                return redirect(url_for("downloads")) 
        except Exception as e:
            # Handle exceptions, maybe show an error message to the user
            print(f"Error: {e}")

    # Retrieve the user from the database based on the user_id stored in the session
    user = User.query.filter_by(id=session['user_id']).first()

    
    return render_template('download.html', username=user.username)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Query the database for the user
        user = User.query.filter_by(email=email).first()

        # Check if the user exists and the password is correct
        if user and user.check_password(password):
            # Store the user ID in the session for authentication
            session['user_id'] = user.id
            

            # Redirect to the download page after successful login
            return redirect(url_for('downloads'))  
        flash('Invalid username or password.', 'error')

    # Redirect to the login page if login fails
    return render_template('login.html')





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if the username or email already exists in the database
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('register.html', error="Username or email already exists. Please choose a different one.")

        # Create a new user and save to the database
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route("/download", methods=["POST"])
def download_music_route():
    if request.method == "POST":
        url = request.form.get("music-url")
        save_dir = "/Users/king-omar/Desktop/AudioGrabber/Music"
        s3_bucket_name = "cloudmediadownloader"

        try:
            # Download music and get file information
            file_info = audiograbber_download_music(url, save_dir, s3_bucket_name)

            # Upload to S3
            if file_info:
                source = file_info['source']

                # Create an S3 client
                s3 = boto3.client('s3', aws_access_key_id='AKIAQ4SE3SQ4Z4ITQD25', aws_secret_access_key='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') 

                

                # Store file information in the database
                user_id = session.get('user_id')

                # Redirect to the downloads page after successful download
                return redirect(url_for("downloads"))
        except Exception as e:
        
            print(f"Error: {e}")

            # Log the error
            current_app.logger.error(f"Error uploading to S3: {e}")

            
            flash("Error uploading to S3. Please try again.", "error")

    # Redirect to the downloads page if there's an error or if the download was unsuccessful
    return redirect(url_for("downloads"))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
