import os
from flask import Flask, redirect, url_for, render_template
from flask_dance.contrib.google import make_google_blueprint, google
from flask_pymongo import PyMongo
from dotenv import load_dotenv

# Laad variabelen uit .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# MongoDB configuratie
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Google OAuth configuratie
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="test_index"
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/test")
def test_index():
    return render_template("test_index.html", google=google)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
