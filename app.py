from flask import Flask, render_template, request, redirect, url_for, flash, flash
from models import db, Client, User, EmailTemplate, EmailLog
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import smtplib
from email.mime.text import MIMEText
from utils import EMAIL_SIGNATURE, plaintext_to_html, strip_cid_images,send_and_save_email, fetch_emails_for_client
import os
import datetime
from import_emails import poll_and_store_incoming
from dotenv import load_dotenv
load_dotenv()

BCC_EMAIL = 'bcc@divi-design.co.uk'

app = Flask(__name__)
app.jinja_env.filters['strip_cid_images'] = strip_cid_images
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

#  User Registration
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
            return redirect(url_for('dashboard'))
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
    clients = Client.query.all()
    return render_template('dashboard.html', client_count=len(clients), clients=clients)

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
        postcode = request.form['postcode']
        client = Client(name=name, email=email, address=address, service=service, postcode=postcode)
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
        client.postcode = request.form['postcode']
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


# --- Email Sending ---
@app.route('/send_email/<int:client_id>', methods=['GET', 'POST'])
@login_required
def send_email(client_id):
    client = Client.query.get_or_404(client_id)
    templates = EmailTemplate.query.all()
    if request.method == 'POST':
        template_id = int(request.form['template'])
        tpl = EmailTemplate.query.get_or_404(template_id)
        subject = request.form.get('subject') or tpl.subject
        body = request.form.get('body') or tpl.body
        subject = subject.replace('{{name}}', client.name or '').replace('{{service}}', client.service or '')
        body = body.replace('{{name}}', client.name or '').replace('{{service}}', client.service or '')
        html_body = plaintext_to_html(body) + EMAIL_SIGNATURE
        try:
            send_and_save_email(subject, html_body, client.email, BCC_EMAIL)
            flash('Email sent successfully!', 'success')
        except Exception as e:
            flash(f'Failed to send email: {e}', 'danger')
        return redirect(url_for('send_email', client_id=client.id))
    return render_template('send_email.html', client=client, templates=templates)

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

@app.route('/clients/<int:client_id>/emails')
@login_required
def client_emails(client_id):
    client = Client.query.get_or_404(client_id)
    poll_and_store_incoming()
    emails = EmailLog.query.filter(
        (EmailLog.from_addr == client.email) | (EmailLog.to_addr == client.email)
    ).order_by(EmailLog.date.desc()).limit(50).all()
    return render_template('client_emails.html', client=client, emails=emails)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
