from flask import Flask, render_template, request, redirect, url_for, flash, flash
from models import db, Client, User, EmailTemplate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
load_dotenv()

EMAIL_SIGNATURE = """
<br>--<br>
<b>Kind regards,</b><br>
<img src="https://i.imgur.com/x2rTMJw.png" width="120">
<br>
<b>Divi Design </b><br>
<a href="https://divi-design.co.uk">https://divi-design.co.uk</a>
"""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-secret'
db.init_app(app)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- User Registration (use once for first admin user, then remove if you wish) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('User registered! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('clients'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- CRM routes, now all protected by login ---
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('welcome.html')

@app.route('/dashboard')
@login_required
def dashboard():
    client_count = Client.query.count()
    return render_template('dashboard.html', client_count=client_count)

@app.route('/clients')
@login_required
def clients():
    client_list = Client.query.all()
    return render_template('clients.html', clients=client_list)

@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        service = request.form['service']
        address = request.form['address']
        client = Client(name=name, email=email, address=address, service=service)
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('clients'))
    return render_template('add_client.html')

@app.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.email = request.form['email']
        address = request.form['address']
        client.service = request.form['service']
        db.session.commit()
        return redirect(url_for('clients'))
    return render_template('edit_client.html', client=client)

@app.route('/clients/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('clients'))

@app.route('/send_email', methods=['GET', 'POST'])
@login_required
def send_email():
    clients = Client.query.all()
    templates = EmailTemplate.query.all()
    message = ''
    if request.method == 'POST':
        client_id = int(request.form['client'])
        template_id = int(request.form['template'])
        client = Client.query.get_or_404(client_id)
        tpl = EmailTemplate.query.get_or_404(template_id)
        subject = request.form.get('subject') or tpl.subject
        body = request.form.get('body') or tpl.body

        subject = subject.replace('{{name}}', client.name).replace('{{service}}', client.service or '')
        body = body.replace('{{name}}', client.name).replace('{{service}}', client.service or '')
        body += EMAIL_SIGNATURE
        sender = os.environ.get('EMAIL_USER')
        password = os.environ.get('EMAIL_PASS')
        recipient = client.email
        print(f"From: {sender}")
        print(f"To: {recipient}")

        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient



        try:
            with smtplib.SMTP('smtp-relay.brevo.com', 587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(sender, password)
                smtp.sendmail(sender, [recipient], msg.as_string())
            flash('Email sent successfully!', 'success')
        except Exception as e:
            flash(f'Failed to send email: {e}', 'danger')
        return redirect(url_for('send_email'))

    return render_template('send_email.html', clients=clients, templates=templates)

@app.route('/templates')
@login_required
def templates():
    templates = EmailTemplate.query.all()
    return render_template('templates.html', templates=templates)

@app.route('/templates/add', methods=['GET', 'POST'])
@login_required
def add_template():
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        body = request.form['body']
        template = EmailTemplate(name=name, subject=subject, body=body)
        db.session.add(template)
        db.session.commit()
        flash("Template added.", "success")
        return redirect(url_for('templates'))
    return render_template('add_template.html')

@app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.name = request.form['name']
        template.subject = request.form['subject']
        template.body = request.form['body']
        db.session.commit()
        flash("Template updated.", "success")
        return redirect(url_for('templates'))
    return render_template('edit_template.html', template=template)

@app.route('/templates/delete/<int:template_id>', methods=['POST'])
@login_required
def delete_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash("Template deleted.", "success")
    return redirect(url_for('templates'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
