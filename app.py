import os
import sqlite3
from flask import Flask, render_template, request, redirect, flash, send_from_directory, session

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "zip"}
MAX_FILE_SIZE = 10 * 1024 * 1024

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

app = Flask(__name__)
app.secret_key = "secretkey"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            index_number TEXT UNIQUE,
            course_code TEXT,
            filename TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET", "POST"])
def submit():
    if request.method == "POST":

        name = request.form["name"]
        index = request.form["index"]
        course = request.form["course"]
        file = request.files["file"]

        if not file or not allowed_file(file.filename):
            flash("Invalid file format")
            return redirect("/")

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{index}_{course}.{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:

            c.execute(
                "INSERT INTO submissions (full_name,index_number,course_code,filename) VALUES (?,?,?,?)",
                (name, index, course, filename),
            )

            conn.commit()

        except sqlite3.IntegrityError:
            flash("Submission already exists for this index number")
            conn.close()
            return redirect("/")

        conn.close()

        file.save(filepath)

        flash("Assignment submitted successfully")

        return redirect("/")

    return render_template("submit.html")


@app.route("/admin/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin"] = True
            return redirect("/admin/dashboard")

        flash("Invalid login")

    return render_template("login.html")


@app.route("/admin/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM submissions")
    data = c.fetchall()

    conn.close()

    return render_template("dashboard.html", submissions=data)


@app.route("/download/<filename>")
def download(filename):

    if "admin" not in session:
        return redirect("/admin/login")

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)