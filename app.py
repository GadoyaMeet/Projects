# from flask import Flask, render_template, request
# import sqlite3
# from datetime import datetime

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html', selected_date='', no_data=False)

# @app.route('/attendance', methods=['POST'])
# def attendance():
#     selected_date = request.form.get('selected_date')
#     selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
#     formatted_date = selected_date_obj.strftime('%Y-%m-%d')

#     conn = sqlite3.connect('attendance.db')
#     cursor = conn.cursor()

#     cursor.execute("SELECT name, time FROM attendance WHERE date = ?", (formatted_date,))
#     attendance_data = cursor.fetchall()

#     conn.close()

#     if not attendance_data:
#         return render_template('index.html', selected_date=selected_date, no_data=True)
    
#     return render_template('index.html', selected_date=selected_date, attendance_data=attendance_data)

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, render_template, request, flash, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

@app.route('/')
def index():
    return render_template('index.html', selected_date='', no_data=False)

@app.route('/attendance', methods=['POST'])
def attendance():
    selected_date = request.form.get('selected_date')

    if not selected_date:
        flash("Please select a valid date.")
        return redirect(url_for('index'))

    try:
        selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format.")
        return redirect(url_for('index'))

    formatted_date = selected_date_obj.strftime('%Y-%m-%d')

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, time FROM attendance WHERE date = ?", (formatted_date,))
    attendance_data = cursor.fetchall()
    conn.close()

    if not attendance_data:
        return render_template('index.html', selected_date=selected_date, no_data=True)
    
    return render_template('index.html', selected_date=selected_date, attendance_data=attendance_data)

if __name__ == '__main__':
    app.run(debug=True)
