from flask import Flask, render_template, request, jsonify
import razorpay
import os

app = Flask(__name__)

# Razorpay Keys from Render Environment
RAZORPAY_KEY_ID = "rzp_test_SKIqg97Xg9C4BV"
RAZORPAY_KEY_SECRET = "HGyuQ62TT9F2Qxm3GBLkto26"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- PAYMENT PAGE ----------------
@app.route("/payment")
def payment_page():
    return render_template("payment.html", key_id=RAZORPAY_KEY_ID)


# ---------------- CREATE ORDER ----------------
@app.route("/create_order", methods=["POST"])
def create_order():
    amount = int(request.form["amount"]) * 100  # Convert to paise

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify(order)


if __name__ == "__main__":
    app.run()
