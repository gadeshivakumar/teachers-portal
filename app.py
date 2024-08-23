from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import hashlib
app = Flask(__name__)
app.secret_key = 'your_secret_key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)

    student = db.relationship('Student', backref=db.backref('marks', lazy=True))

    def __repr__(self):
        return f"Marks('{self.student_id}', '{self.subject}', '{self.marks}')"


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Teacher('{self.name}', '{self.email}')"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Student('{self.name}', '{self.roll_number}')"
    
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    present = db.Column(db.Boolean, default=False)

    student = db.relationship('Student', backref=db.backref('attendance', lazy=True))

    def __repr__(self):
        return f"Attendance('{self.student_id}', '{self.present}')"




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        # Hash the password before storing it
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        department = request.form['department']
        subject = request.form['subject']
        
        # Check if email or subject already exists in the database
        existing_teacher_email = Teacher.query.filter_by(email=email).first()
        existing_teacher_subject = Teacher.query.filter_by(subject=subject).first()
        if existing_teacher_email:
            return "Email already exists. Please choose a different one."
                
        # Create a new teacher object and add it to the database
        new_teacher = Teacher(name=name, email=email, password=password, department=department, subject=subject)
        db.session.add(new_teacher)
        db.session.commit()
        
        return redirect(url_for('signup_success'))
    return render_template('signup.html')

@app.route('/signup_success')
def signup_success():
    return "Signup successful!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Find the user by email
        teacher = Teacher.query.filter_by(email=email).first()
        # Verify the hashed password
        if teacher and teacher.password == hashlib.sha256(password.encode()).hexdigest():
            # Store user ID in session
            session['user_id'] = teacher.id
            return redirect(url_for('index'))
        else:
            return "Invalid email or password. Please try again."
    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    
    if 'user_id' in session:
        user_id = session['user_id']
        
        teacher = Teacher.query.get(user_id)
        return render_template('dashboard.html', teacher=teacher)
    else:
        return redirect(url_for('login'))


# @app.route('/portal')
# def por():
#     return render_template('portal.html')

@app.route('/students_list')
def sl():
    students = Student.query.all()
    present_absent_counts = {}
    for student in students:
        present_count = Attendance.query.filter_by(student_id=student.id, present=True).count()
        absent_count = Attendance.query.filter_by(student_id=student.id, present=False).count()
        total_days = present_count + absent_count
        attendance_percentage = (present_count / total_days) * 100 if total_days != 0 else 0
        present_absent_counts[student.id] = {'present': present_count, 'absent': absent_count, 'attendance_percentage': attendance_percentage}
    return render_template('students_list.html', students=students, present_absent_counts=present_absent_counts)

@app.route('/index')
def index():
    students = Student.query.all()
    present_absent_counts = {}
    for student in students:
        present_count = Attendance.query.filter_by(student_id=student.id, present=True).count()
        absent_count = Attendance.query.filter_by(student_id=student.id, present=False).count()
        total_days = present_count + absent_count
        attendance_percentage = (present_count / total_days) * 100 if total_days != 0 else 0
        present_absent_counts[student.id] = {'present': present_count, 'absent': absent_count, 'attendance_percentage': attendance_percentage}
    return render_template('index.html', students=students, present_absent_counts=present_absent_counts)

@app.route('/')
def land():
    return render_template('landing.html')

@app.route('/attend', methods=['GET', 'POST'])
def attend():
    if request.method == 'POST':
        for student in Student.query.all():
            present = bool(request.form.get(f'present_{student.id}'))
            attendance = Attendance(student_id=student.id, present=present)
            db.session.add(attendance)
        db.session.commit()
        return redirect(url_for('index'))
    
    students = Student.query.all()
    return render_template('attend.html', students=students)




@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        department = request.form['department']
        section = request.form['section']
        
        # Check if roll number already exists in the database
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            return "Roll number already exists. Please choose a different one."
        
        # Create a new student object and add it to the database
        new_student = Student(name=name, roll_number=roll_number, department=department, section=section)
        db.session.add(new_student)
        db.session.commit()
        
        return redirect(url_for('index'))
    return render_template('addStudent.html')

# @app.route('/delete_student/<int:id>')
# def delete_student(id):
#     student_to_delete = Student.query.get_or_404(id)
#     db.session.delete(student_to_delete)
#     db.session.commit()
#     return redirect(url_for('index'))



@app.route('/delete_student/<int:id>', methods=['POST', 'DELETE'])  # Allow both POST and DELETE methods
def delete_student(id):
    if request.method in ['POST', 'DELETE']:  # Check for POST or DELETE method
        student_to_delete = Student.query.get_or_404(id)
        db.session.delete(student_to_delete)
        db.session.commit()
        return redirect(url_for('sl'))  # Redirect to students list page after deletion


@app.route('/marks', methods=['GET', 'POST'])
def marks():
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        marks = request.form['marks']

        new_marks = Marks(student_id=student_id, subject=subject, marks=marks)
        db.session.add(new_marks)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    students = Student.query.all()
    return render_template('marks.html', students=students)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
