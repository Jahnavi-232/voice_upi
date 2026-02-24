from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import razorpay
import base64
import cv2
import numpy as np

app = Flask(__name__)

# 🔥 Increase upload limit (Fix for Request Entity Too Large)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # -------- USERS TABLE --------
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """)

    # Check users columns
    c.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in c.fetchall()]

    if "face_image" not in user_columns:
        c.execute("ALTER TABLE users ADD COLUMN face_image TEXT")

    # -------- CONTACTS TABLE --------
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY
        )
    """)

    # Check contacts columns
    c.execute("PRAGMA table_info(contacts)")
    contact_columns = [col[1] for col in c.fetchall()]

    if "name" not in contact_columns:
        c.execute("ALTER TABLE contacts ADD COLUMN name TEXT")

    if "upi_id" not in contact_columns:
        c.execute("ALTER TABLE contacts ADD COLUMN upi_id TEXT")

    conn.commit()
    conn.close()
init_db()


# ---------------- RAZORPAY ----------------

RAZORPAY_KEY_ID = "rzp_test_xxxxx"   # replace later
RAZORPAY_SECRET = "your_secret"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/addcontact")
def add_contact_page():
    return render_template("addcontact.html")

@app.route("/payment")
def payment_page():
    return render_template("payment.html", key_id=RAZORPAY_KEY_ID)


# ---------------- REGISTER USER ----------------

@app.route("/register_user", methods=["POST"])
def register_user():
    name = request.form["name"]
    email = request.form["email"]
    face_image = request.form["face"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users")  # only one user allowed
    c.execute("INSERT INTO users (name,email,face_image) VALUES (?,?,?)",
              (name, email, face_image))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# ---------------- ADD CONTACT ----------------

@app.route("/add_contact", methods=["POST"])
def add_contact():
    name = request.form["name"].lower()
    upi = request.form["upi"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO contacts (name,upi_id) VALUES (?,?)",
              (name, upi))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# ---------------- FACE VERIFICATION ----------------

@app.route("/verify_face", methods=["POST"])
def verify_face():

    live_image = request.form["image"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT face_image FROM users LIMIT 1")
    stored = c.fetchone()
    conn.close()

    if not stored:
        return jsonify({"status": "no_user"})

    stored_image = stored[0]

    def decode_image(data):
        img_data = base64.b64decode(data.split(",")[1])
        nparr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    img1 = decode_image(stored_image)
    img2 = decode_image(live_image)

    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))

    diff = cv2.absdiff(img1, img2)
    score = np.mean(diff)

    if score < 45:
        return jsonify({"status": "matched"})
    else:
        return jsonify({"status": "not_matched"})


# ---------------- CREATE PAYMENT ORDER ----------------

@app.route("/create_order", methods=["POST"])
def create_order():
    amount = int(request.form["amount"]) * 100

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify(order)


if __name__ == "__main__":
    app.run()