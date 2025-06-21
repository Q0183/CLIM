import os
from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# MongoDB setup
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
users = mongo.db.users
records = mongo.db.records

# OAuth setup
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    redirect_url="/login/callback",
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")


@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email = resp.json()["email"]
    user = users.find_one({"email": email})
    if not user:
        token = str(uuid.uuid4())
        users.insert_one({"email": email, "token": token})
    user = users.find_one({"email": email})
    user_records = list(records.find({"email": email}))
    return render_template("index.html", email=email, token=user["token"], records=user_records)


@app.route("/add", methods=["POST"])
def add_record():
    if not google.authorized:
        return redirect(url_for("google.login"))
    email = google.get("/oauth2/v2/userinfo").json()["email"]
    fqdn = request.form["fqdn"]
    ip = request.form["ip"]
    records.insert_one({"email": email, "fqdn": fqdn, "ip": ip})
    return redirect(url_for("index"))


@app.route("/api/v1/update/<token>", methods=["POST"])
def update_record(token):
    data = request.get_json()
    fqdn = data.get("fqdn")
    ip = data.get("ip")
    user = users.find_one({"token": token})
    if not user:
        return jsonify({"error": "Invalid token"}), 403
    existing = records.find_one({"email": user["email"], "fqdn": fqdn})
    if existing:
        records.update_one({"_id": existing["_id"]}, {"$set": {"ip": ip}})
        return jsonify({"status": "updated"}), 200
    else:
	records.insert_one({"email": user["email"], "fqdn": fqdn, "ip": ip})
        return jsonify({"status": "created"}), 201


@app.route("/api/v1/delete/<token>", methods=["POST"])
def delete_record(token):
    data = request.get_json()
    fqdn = data.get("fqdn")
    user = users.find_one({"token": token})
    if not user:
        return jsonify({"error": "Invalid token"}), 403
    result = records.delete_one({"email": user["email"], "fqdn": fqdn})
    if result.deleted_count > 0:
        return jsonify({"status": "deleted"}), 200
    else:
	return jsonify({"status": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

