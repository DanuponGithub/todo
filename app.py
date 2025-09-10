import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ---- DB URL (SQLite สำหรับรัน local, เปลี่ยนเป็น Postgres อัตโนมัติเมื่อมี DATABASE_URL) ----
db_url = os.getenv("DATABASE_URL", "sqlite:///todolist.db")

# แปลง driver เป็น psycopg v3 เสมอ
if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://") and "+psycopg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# เติม sslmode=require ถ้ายังไม่มี
if db_url.startswith("postgresql") and "sslmode=" not in db_url:
    db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    todos = Todo.query.order_by(Todo.created_at.desc())
    if q:
        todos = todos.filter(Todo.title.ilike(f"%{q}%"))
    return render_template("index.html", todos=todos.all(), q=q)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        db.session.add(Todo(title=title))
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    t = Todo.query.get_or_404(todo_id)
    t.is_done = not t.is_done
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    t = Todo.query.get_or_404(todo_id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)