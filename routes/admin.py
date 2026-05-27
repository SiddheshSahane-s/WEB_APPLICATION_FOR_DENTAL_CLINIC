from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from models import db, User, Patient, Appointment, Prescription, MedicalReport, Invoice, Payment, BlogPost, Notification, Service, Speciality, Testimonial, ActivityLog
import json, os, random, string
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/secure-admin-panel')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'dentist', 'receptionist']:
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Super admin access required.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated

# ── DASHBOARD ──────────────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    today_appointments = Appointment.query.filter_by(appointment_date=date.today()).count()
    pending_appointments = Appointment.query.filter_by(status='pending').count()
    confirmed_appointments = Appointment.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(db.func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
    monthly_revenue = db.session.query(db.func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        db.func.strftime('%Y-%m', Invoice.created_at) == datetime.utcnow().strftime('%Y-%m')
    ).scalar() or 0
    active_reminders = Notification.query.filter_by(status='pending').count()
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    # Monthly appointments for chart
    monthly_data = []
    for i in range(6):
        month = datetime.utcnow() - timedelta(days=30*i)
        count = Appointment.query.filter(
            db.func.strftime('%Y-%m', Appointment.appointment_date) == month.strftime('%Y-%m')
        ).count()
        monthly_data.append({'month': month.strftime('%b %Y'), 'count': count})
    monthly_data.reverse()
    return render_template('admin/dashboard.html',
        total_patients=total_patients,
        total_appointments=total_appointments,
        today_appointments=today_appointments,
        pending_appointments=pending_appointments,
        confirmed_appointments=confirmed_appointments,
        total_revenue=total_revenue,
        monthly_revenue=monthly_revenue,
        active_reminders=active_reminders,
        recent_appointments=recent_appointments,
        recent_patients=recent_patients,
        monthly_data=json.dumps(monthly_data)
    )

# ── PATIENTS ────────────────────────────────────────────────────────────────
@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Patient.query.join(User)
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f'%{search}%'), User.phone.ilike(f'%{search}%'),
                   User.email.ilike(f'%{search}%'), Patient.patient_code.ilike(f'%{search}%'))
        )
    patients = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/patients.html', patients=patients, search=search)

@admin_bp.route('/patients/<int:patient_id>')
@login_required
@admin_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()
    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.created_at.desc()).all()
    invoices = Invoice.query.filter_by(patient_id=patient_id).order_by(Invoice.created_at.desc()).all()
    return render_template('admin/patient_detail.html', patient=patient,
                           appointments=appointments, prescriptions=prescriptions,
                           reports=reports, invoices=invoices)

@admin_bp.route('/patients/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_patient():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('admin/add_patient.html')
        user = User(name=name, email=email, phone=phone, role='patient')
        user.set_password(phone[-4:] if phone and len(phone) >= 4 else '1234')
        db.session.add(user)
        db.session.flush()
        code = 'MD' + ''.join(random.choices(string.digits, k=6))
        patient = Patient(
            user_id=user.id, patient_code=code,
            age=request.form.get('age', type=int),
            gender=request.form.get('gender'),
            blood_group=request.form.get('blood_group'),
            address=request.form.get('address'),
            allergies=request.form.get('allergies'),
            medical_history=request.form.get('medical_history'),
            dental_history=request.form.get('dental_history')
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient {name} added successfully! Code: {code}', 'success')
        return redirect(url_for('admin.patients'))
    return render_template('admin/add_patient.html')

@admin_bp.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        patient.user.name = request.form.get('name', patient.user.name)
        patient.user.phone = request.form.get('phone', patient.user.phone)
        patient.age = request.form.get('age', type=int) or patient.age
        patient.gender = request.form.get('gender', patient.gender)
        patient.blood_group = request.form.get('blood_group', patient.blood_group)
        patient.address = request.form.get('address', patient.address)
        patient.allergies = request.form.get('allergies', patient.allergies)
        patient.medical_history = request.form.get('medical_history', patient.medical_history)
        patient.dental_history = request.form.get('dental_history', patient.dental_history)
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.patient_detail', patient_id=patient_id))
    return render_template('admin/edit_patient.html', patient=patient)

@admin_bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    user = patient.user
    db.session.delete(patient)
    db.session.delete(user)
    db.session.commit()
    flash('Patient deleted.', 'success')
    return redirect(url_for('admin.patients'))

# ── APPOINTMENTS ─────────────────────────────────────────────────────────────
@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    query = Appointment.query
    if status:
        query = query.filter_by(status=status)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=filter_date)
        except:
            pass
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.asc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/appointments.html', appointments=appointments, status=status, date_filter=date_filter)

@admin_bp.route('/appointments/<int:apt_id>/action', methods=['POST'])
@login_required
@admin_required
def appointment_action(apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    action = request.form.get('action')
    if action == 'confirm':
        apt.status = 'confirmed'
        apt.confirmed_at = datetime.utcnow()
        flash('Appointment confirmed!', 'success')
    elif action == 'cancel':
        apt.status = 'cancelled'
        apt.cancelled_at = datetime.utcnow()
        apt.cancel_reason = request.form.get('reason', '')
        flash('Appointment cancelled.', 'info')
    elif action == 'complete':
        apt.status = 'completed'
        flash('Appointment marked as completed!', 'success')
    elif action == 'reschedule':
        new_date = request.form.get('new_date')
        new_time = request.form.get('new_time')
        if new_date and new_time:
            apt.appointment_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            apt.appointment_time = datetime.strptime(new_time, '%H:%M').time()
            apt.status = 'confirmed'
            flash('Appointment rescheduled!', 'success')
    db.session.commit()
    return redirect(url_for('admin.appointments'))

# ── PRESCRIPTIONS ────────────────────────────────────────────────────────────
@admin_bp.route('/prescriptions')
@login_required
@admin_required
def prescriptions():
    page = request.args.get('page', 1, type=int)
    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/prescriptions.html', prescriptions=prescriptions)

@admin_bp.route('/prescriptions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_prescription():
    patients = Patient.query.join(User).order_by(User.name).all()
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        appointment_id = request.form.get('appointment_id', type=int)
        code = 'RX' + ''.join(random.choices(string.digits, k=8))
        rx = Prescription(
            prescription_code=code,
            patient_id=patient_id,
            appointment_id=appointment_id if appointment_id else None,
            diagnosis=request.form.get('diagnosis'),
            medications=request.form.get('medications'),
            instructions=request.form.get('instructions'),
        )
        follow_up = request.form.get('follow_up_date')
        if follow_up:
            rx.follow_up_date = datetime.strptime(follow_up, '%Y-%m-%d').date()
        db.session.add(rx)
        db.session.commit()
        flash('Prescription created successfully!', 'success')
        return redirect(url_for('admin.prescriptions'))
    return render_template('admin/add_prescription.html', patients=patients)

# ── BILLING ───────────────────────────────────────────────────────────────────
@admin_bp.route('/billing')
@login_required
@admin_required
def billing():
    page = request.args.get('page', 1, type=int)
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    total_paid = db.session.query(db.func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
    total_unpaid = db.session.query(db.func.sum(Invoice.total)).filter_by(status='unpaid').scalar() or 0
    return render_template('admin/billing.html', invoices=invoices, total_paid=total_paid, total_unpaid=total_unpaid)

@admin_bp.route('/billing/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_invoice():
    patients = Patient.query.join(User).order_by(User.name).all()
    if request.method == 'POST':
        inv_num = 'INV' + datetime.utcnow().strftime('%Y%m%d') + ''.join(random.choices(string.digits, k=4))
        patient_id = request.form.get('patient_id', type=int)
        total = request.form.get('total', type=float) or 0
        invoice = Invoice(
            invoice_number=inv_num,
            patient_id=patient_id,
            items=request.form.get('items', '[]'),
            subtotal=request.form.get('subtotal', type=float) or total,
            discount=request.form.get('discount', type=float) or 0,
            total=total,
            status='unpaid',
            notes=request.form.get('notes')
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice created!', 'success')
        return redirect(url_for('admin.billing'))
    return render_template('admin/add_invoice.html', patients=patients)

@admin_bp.route('/billing/<int:inv_id>/pay', methods=['POST'])
@login_required
@admin_required
def mark_paid(inv_id):
    invoice = Invoice.query.get_or_404(inv_id)
    invoice.status = 'paid'
    invoice.paid_at = datetime.utcnow()
    invoice.payment_method = request.form.get('method', 'cash')
    payment = Payment(invoice_id=inv_id, amount=invoice.total, method=invoice.payment_method)
    db.session.add(payment)
    db.session.commit()
    flash('Payment recorded!', 'success')
    return redirect(url_for('admin.billing'))

# ── BLOG ──────────────────────────────────────────────────────────────────────
@admin_bp.route('/blog')
@login_required
@admin_required
def blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)

@admin_bp.route('/blog/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '') if title else ''
        # Ensure unique slug
        count = BlogPost.query.filter_by(slug=slug).count()
        if count > 0:
            slug = slug + '-' + str(count)
        post = BlogPost(
            title=title,
            slug=slug,
            excerpt=request.form.get('excerpt'),
            content=request.form.get('content'),
            category=request.form.get('category'),
            tags=request.form.get('tags'),
            author_id=current_user.id,
            is_published=request.form.get('publish') == 'on',
            published_at=datetime.utcnow() if request.form.get('publish') == 'on' else None
        )
        db.session.add(post)
        db.session.commit()
        flash('Blog post created!', 'success')
        return redirect(url_for('admin.blog'))
    return render_template('admin/add_blog.html')

@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form.get('title', post.title)
        post.excerpt = request.form.get('excerpt', post.excerpt)
        post.content = request.form.get('content', post.content)
        post.category = request.form.get('category', post.category)
        post.tags = request.form.get('tags', post.tags)
        was_published = post.is_published
        post.is_published = request.form.get('publish') == 'on'
        if post.is_published and not was_published:
            post.published_at = datetime.utcnow()
        db.session.commit()
        flash('Blog post updated!', 'success')
        return redirect(url_for('admin.blog'))
    return render_template('admin/edit_blog.html', post=post)

@admin_bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'success')
    return redirect(url_for('admin.blog'))

# ── SERVICES & SPECIALITIES ───────────────────────────────────────────────────
@admin_bp.route('/specialities')
@login_required
@admin_required
def specialities():
    specs = Speciality.query.order_by(Speciality.name).all()
    return render_template('admin/specialities.html', specialities=specs)

@admin_bp.route('/specialities/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_speciality():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = name.lower().replace(' ', '-').replace(',', '').replace('.', '')
        # Handle Image
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(upload_path)
            image_filename = 'uploads/' + filename
        
        spec = Speciality(
            name=name,
            slug=slug,
            description=request.form.get('description'),
            symptoms=request.form.get('symptoms'),
            treatment_methods=request.form.get('treatment_methods'),
            faq=request.form.get('faq'),
            icon=request.form.get('icon', 'fa-tooth'),
            image=image_filename,
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(spec)
        db.session.commit()
        flash('Speciality added successfully!', 'success')
        return redirect(url_for('admin.specialities'))
    return render_template('admin/add_speciality.html')

@admin_bp.route('/specialities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_speciality(id):
    spec = Speciality.query.get_or_404(id)
    if request.method == 'POST':
        spec.name = request.form.get('name', spec.name)
        spec.slug = spec.name.lower().replace(' ', '-').replace(',', '').replace('.', '')
        spec.description = request.form.get('description', spec.description)
        spec.symptoms = request.form.get('symptoms', spec.symptoms)
        spec.treatment_methods = request.form.get('treatment_methods', spec.treatment_methods)
        spec.faq = request.form.get('faq', spec.faq)
        spec.icon = request.form.get('icon', spec.icon)
        spec.is_active = request.form.get('is_active') == 'on'
        
        # Handle Image
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(upload_path)
            spec.image = 'uploads/' + filename

        db.session.commit()
        flash('Speciality updated!', 'success')
        return redirect(url_for('admin.specialities'))
    return render_template('admin/edit_speciality.html', spec=spec)

@admin_bp.route('/specialities/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_speciality(id):
    spec = Speciality.query.get_or_404(id)
    db.session.delete(spec)
    db.session.commit()
    flash('Speciality deleted!', 'success')
    return redirect(url_for('admin.specialities'))


@admin_bp.route('/services')
@login_required
@admin_required
def services():
    services = Service.query.order_by(Service.name).all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    if request.method == 'POST':
        service = Service(
            name=request.form.get('name'),
            description=request.form.get('description'),
            duration_minutes=request.form.get('duration', type=int),
            base_price=request.form.get('price', type=float),
            category=request.form.get('category'),
            icon=request.form.get('icon', 'fa-stethoscope'),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/add_service.html')

@admin_bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.name = request.form.get('name', service.name)
        service.description = request.form.get('description', service.description)
        service.duration_minutes = request.form.get('duration', type=int) or service.duration_minutes
        service.base_price = request.form.get('price', type=float) or service.base_price
        service.category = request.form.get('category', service.category)
        service.icon = request.form.get('icon', service.icon)
        service.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash('Service updated!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/edit_service.html', service=service)

@admin_bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted!', 'success')
    return redirect(url_for('admin.services'))

@admin_bp.route('/users')
@login_required
@super_admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@super_admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['patient', 'dentist', 'receptionist', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Role updated to {new_role}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/activity-logs')
@login_required
@super_admin_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('admin/activity_logs.html', logs=logs)

# ── REMINDERS / WHATSAPP ─────────────────────────────────────────────────────
@admin_bp.route('/reminders')
@login_required
@admin_required
def reminders():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/reminders.html', notifications=notifications)

@admin_bp.route('/reminders/send/<int:apt_id>', methods=['POST'])
@login_required
@admin_required
def send_reminder(apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    from routes.api import send_whatsapp_reminder
    result = send_whatsapp_reminder(apt)
    if result:
        flash('Reminder sent successfully!', 'success')
    else:
        flash('Reminder queued (WhatsApp API not configured).', 'info')
    return redirect(url_for('admin.appointments'))

# ── SETTINGS ─────────────────────────────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    from models import SystemSetting
    
    if request.method == 'POST':
        keys_to_update = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_FROM']
        
        for key in keys_to_update:
            value = request.form.get(key, '').strip()
            # If it's a password field and empty, don't update it to preserve existing token
            if key == 'TWILIO_AUTH_TOKEN' and not value:
                continue
                
            setting = SystemSetting.query.filter_by(key=key).first()
            if not setting:
                setting = SystemSetting(key=key, value=value)
                db.session.add(setting)
            else:
                setting.value = value
                
        db.session.commit()
        flash('System settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    # Get all settings
    all_settings = SystemSetting.query.all()
    settings_dict = {s.key: s.value for s in all_settings}
    
    return render_template('admin/settings.html', settings=settings_dict)

# ── API ENDPOINTS FOR AJAX ────────────────────────────────────────────────────
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    return jsonify({
        'patients': Patient.query.count(),
        'appointments_today': Appointment.query.filter_by(appointment_date=date.today()).count(),
        'pending': Appointment.query.filter_by(status='pending').count(),
        'revenue': db.session.query(db.func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
    })
