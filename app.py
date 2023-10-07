from flask import Flask, redirect, url_for, render_template, request, flash, get_flashed_messages
import os
import datetime
import cv2
from database import db, User

app = Flask(__name__)
app.secret_key = "haha"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def readQRCode():
    qr_data = ''
    current_datetime = ''
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    exit_flag = False  # Flag thoat vong lap

    while not exit_flag:
        _, img = cap.read()
        data, one, _ = detector.detectAndDecode(img)
        if data:
            qr_data = data
            current_datetime = datetime.datetime.now()  # Lay du lieu thoi diem quet QR Code
            exit_flag = True
        cv2.imshow('QRCodeScanner app', img)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return qr_data, current_datetime


@app.route("/", methods=["GET", "POST"])
def home_page():
    if request.method == "POST":
        print(request.form)
        if "check_in_button" in request.form and request.form["check_in_button"] == "check_in":
            return redirect(url_for("check_in"))
        elif "check_out_button" in request.form and request.form["check_out_button"] == "check_out":
            return redirect(url_for("check_out"))
    return render_template("home_page.html")


@app.route("/check_in", methods=["GET", "POST"])
def check_in():
    if request.method == "POST":
        # Get guest ID from form data
        guest_id = request.form["id"]
        # Query DB for latest row of data for guest ID
        latest_visit = User.query.filter_by(ID=guest_id).order_by(User.GioVao.desc()).first()

        if latest_visit:
            # Pass latest row of data to update form
            return redirect(url_for("update_form", id=guest_id, latest_visit=latest_visit))
        else:
            # Display form to input new user data
            return redirect(url_for("input_form", id=guest_id))
    return render_template("input_id_form.html")


@app.route("/update/<id>", methods=["GET", "POST"])
def update_form(id):
    latest_visit = User.query.filter_by(ID=id).order_by(User.GioVao.desc()).first()
    if request.method == "POST":
        guest_card, time_in = readQRCode()
        # Insert new row into DB
        new_user = User(
            HoTen=latest_visit.HoTen,
            ID=latest_visit.ID,
            SoDienThoai=request.form.get("phone_number", latest_visit.SoDienThoai),
            LoaiXe=request.form.get("vehicle_type", latest_visit.LoaiXe),
            BienSoXe=request.form.get("vehicle_number", latest_visit.BienSoXe),
            CongTy=request.form.get("company_name", latest_visit.CongTy),
            DiaChi=request.form.get("address", latest_visit.DiaChi),
            BPCanGap=request.form.get("department", latest_visit.BPCanGap),
            NguoiCanGap=request.form.get("who", latest_visit.NguoiCanGap),
            MucDich=request.form.get("purpose", latest_visit.MucDich),
            HDAnToan=bool(request.form.get("instructions", False)),
            MaTheKhach=guest_card,
            GioVao=time_in,
            GioRa=None
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Chúc bạn một ngày làm việc an toàn và hiệu quả!", "success")
        return redirect(url_for("home_page"))
    else:
        return render_template("update_form.html", latest_visit=latest_visit)


@app.route("/input/<id>", methods=["GET", "POST"])
def input_form(id):
    if request.method == "POST":
        guest_card, time_in = readQRCode()
        # Create new user in the database
        user = User(
            ID=id,
            HoTen=request.form["name"],
            SoDienThoai=request.form["phone_number"],
            LoaiXe=request.form["vehicle_type"],
            BienSoXe=request.form["vehicle_number"],
            CongTy=request.form["company_name"],
            DiaChi=request.form["address"],
            BPCanGap=request.form["department"],
            NguoiCanGap=request.form["who"],
            MucDich=request.form["purpose"],
            HDAnToan=bool(request.form.get("instructions", False)),
            MaTheKhach=guest_card,
            GioVao=time_in,
            GioRa=None)
        db.session.add(user)
        db.session.commit()
        flash("Chúc bạn một ngày làm việc an toàn và hiệu quả!", "success")
        return redirect(url_for("home_page"))
    else:
        return render_template("input_form.html")


@app.route("/check_out", methods=["GET", "POST"])
def check_out():
    if request.method == "POST":
        guest_card, time_out = readQRCode()

        # Query DB bang MaTheKhach, GioRa = None
        user = User.query.filter_by(MaTheKhach=guest_card, GioRa=None).first()

        if user:
            # Update GioRa
            user.GioRa = time_out
            db.session.commit()
            flash("Cảm ơn, hẹn gặp lại!", "success")
            print("Flash message:", get_flashed_messages())
            return redirect(url_for("home_page"))
        else:
            return render_template("error.html", message="Invalid QR code")
    else:
        return render_template("check_out.html")


with app.app_context():
    if not os.path.exists("instance/user.db"):
        db.create_all()
        print("CREATED DB")
    app.run(debug=True, port=5001)
