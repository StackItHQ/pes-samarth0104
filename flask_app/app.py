from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        database="superzz",
        user="superjoin",
        password="super"
    )

# Home Route - Display Internships (Read)
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', internships=internships)

# Create Internship (Create)
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        company_name = request.form['company_name']
        job_title = request.form['job_title']
        cgpa_cutoff = request.form['cgpa_cutoff']
        remarks = request.form['remarks']

        if not company_name or not job_title:
            flash('Company Name and Job Title are required!')
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO internships (company_name, job_title, cgpa_cutoff, remarks) VALUES (%s, %s, %s, %s)",
                           (company_name, job_title, cgpa_cutoff, remarks))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html')

# Edit Internship (Update)
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM internships WHERE id = %s', (id,))
    internship = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        company_name = request.form['company_name']
        job_title = request.form['job_title']
        cgpa_cutoff = request.form['cgpa_cutoff']
        remarks = request.form['remarks']

        if not company_name or not job_title:
            flash('Company Name and Job Title are required!')
        else:
            cursor = conn.cursor()
            cursor.execute("UPDATE internships SET company_name = %s, job_title = %s, cgpa_cutoff = %s, remarks = %s WHERE id = %s",
                           (company_name, job_title, cgpa_cutoff, remarks, id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', internship=internship)

# Delete Internship (Delete)
@app.route('/delete/<int:id>', methods=('POST',))
def delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM internships WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Internship deleted successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
