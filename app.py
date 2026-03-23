from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import re
from datetime import datetime

app = Flask(__name__)

# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app.secret_key = 'dev-secret-quizo-app-123'

# Questions (demo 4; expand to 20 later)
questions = [
    {"q": "Python is a ___ language?", "options": ["Compiled", "Interpreted", "Binary", "None"], "ans": "Interpreted"},
    {"q": "HTML stands for?", "options": ["Hyper Trainer Marking Language", "Hyper Text Markup Language", "Hyper Text Marketing Language", "None"], "ans": "Hyper Text Markup Language"},
    {"q": "SQL is used for?", "options": ["Styling", "Database", "Design", "Animation"], "ans": "Database"},
    {"q": "AI stands for?", "options": ["Artificial Intelligence", "Auto Intelligence", "Advanced Input", "None"], "ans": "Artificial Intelligence"}
]

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'])
    return render_template('index.html', login_required=True)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        name = request.form['name']
        score = 0

        for i, q in enumerate(questions):
            if request.form.get(f"q{i}") == q["ans"]:
                score += 1

        percentage = (score / len(questions)) * 100

        safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')[:50]
        
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, score) VALUES (?, ?)", (name, percentage))
        conn.commit()
        conn.close()

        safe_filename = safe_name
        if percentage >= 65:
            cert_filename = generate_certificate(safe_name, percentage, current_date)
            return render_template('certificate.html', cert_filename=cert_filename, name=name)
        return render_template('result.html', name=name, score=percentage, date=current_date, username=session['username'])

    if 'user_id' not in session:
        return redirect('/login')
    return render_template('quiz.html', questions=questions)

from reportlab.lib.utils import ImageReader
def generate_certificate(name, score, date):
    template_path = "static/certificate.png"
    cert_path = f"certificates/{name}_cert.pdf"
    
    c = canvas.Canvas(cert_path, pagesize=(595, 842))  # A4 exact
    
    # Load PNG as background (full size)
    img = ImageReader(template_path)
    c.drawImage(img, 40, 40, width=515, height=762, mask='auto')  # Fit A4, adjust if PNG is not A4
    
    # Date top-left small
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 14)
    c.drawString(60, 790, f"Date: {date}")
    
    # Name just over the golden line
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 52)
    short_name = (name[:20] or "RECIPIENT").upper()
    c.drawCentredString(300, 615, short_name)
    
    c.save()
    return f"{name}_cert.pdf"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO auth (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            error = "Username already exists!"
        finally:
            conn.close()
    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT id FROM auth WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect('/')
        error = "Invalid credentials!"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/download/<filename>')
def download(filename):
    return send_file(f"certificates/{filename}", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

