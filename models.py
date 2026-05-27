from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='patient')  # patient, dentist, receptionist, admin
    is_active = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    preferred_language = db.Column(db.String(10), default='en')

    patient_profile = db.relationship('Patient', backref='user', uselist=False)
    appointments = db.relationship('Appointment', backref='user', lazy='dynamic', foreign_keys='Appointment.user_id')
    blog_posts = db.relationship('BlogPost', backref='author', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_patient(self):
        return self.role == 'patient'

    def __repr__(self):
        return f'<User {self.email}>'


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    patient_code = db.Column(db.String(20), unique=True)
    dob = db.Column(db.Date)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    emergency_contact = db.Column(db.String(20))
    emergency_name = db.Column(db.String(120))
    allergies = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    dental_history = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    insurance_provider = db.Column(db.String(120))
    insurance_id = db.Column(db.String(80))
    qr_code_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', foreign_keys='Appointment.patient_id')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')
    medical_reports = db.relationship('MedicalReport', backref='patient', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='patient', lazy='dynamic')
    notifications = db.relationship('Notification', backref='patient', lazy='dynamic')

    def __repr__(self):
        return f'<Patient {self.patient_code}>'


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=30)
    base_price = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='service', lazy='dynamic')

    def __repr__(self):
        return f'<Service {self.name}>'


class Speciality(db.Model):
    __tablename__ = 'specialities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True)
    description = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    treatment_methods = db.Column(db.Text)
    faq = db.Column(db.Text)
    icon = db.Column(db.String(80))
    image = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Speciality {self.name}>'


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_code = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    # Guest booking fields
    guest_name = db.Column(db.String(120))
    guest_email = db.Column(db.String(120))
    guest_phone = db.Column(db.String(20))
    guest_age = db.Column(db.Integer)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed, rescheduled
    appointment_type = db.Column(db.String(20), default='in-person')  # in-person, video
    notes = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    fee = db.Column(db.Float, default=200.0)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    cancel_reason = db.Column(db.Text)

    prescription = db.relationship('Prescription', backref='appointment', uselist=False)
    invoice = db.relationship('Invoice', backref='appointment', uselist=False)

    def __repr__(self):
        return f'<Appointment {self.appointment_code}>'


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    prescription_code = db.Column(db.String(20), unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    diagnosis = db.Column(db.Text)
    medications = db.Column(db.Text)  # JSON string
    instructions = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    pdf_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Prescription {self.prescription_code}>'


class MedicalReport(db.Model):
    __tablename__ = 'medical_reports'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    title = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(80))  # xray, blood_test, scan, etc.
    file_path = db.Column(db.String(256))
    notes = db.Column(db.Text)
    report_date = db.Column(db.Date, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MedicalReport {self.title}>'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    items = db.Column(db.Text)  # JSON string
    subtotal = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, partial, cancelled
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(256))
    due_date = db.Column(db.Date)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))  # cash, card, upi, online
    transaction_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}>'


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    tags = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    views = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def __repr__(self):
        return f'<BlogPost {self.title}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    type = db.Column(db.String(50))  # whatsapp, email, sms
    message_type = db.Column(db.String(50))  # confirmation, reminder, follow_up, renewal
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    scheduled_for = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<Notification {self.type} - {self.message_type}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200))
    resource = db.Column(db.String(100))
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(120))
    rating = db.Column(db.Integer, default=5)
    message = db.Column(db.Text)
    treatment = db.Column(db.String(120))
    avatar = db.Column(db.String(256))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Testimonial {self.patient_name}>'
