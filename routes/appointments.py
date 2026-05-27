from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from CLINIC.models import db, Appointment, Patient, Service, Notification
import random, string

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

def gen_code():
    return 'APT' + ''.join(random.choices(string.digits, k=8))

@appointments_bp.route('/book', methods=['GET', 'POST'])
def book():
    services = Service.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        service_id = request.form.get('service_id', type=int)
        apt_date_str = request.form.get('appointment_date')
        apt_time_str = request.form.get('appointment_time')
        apt_type = request.form.get('appointment_type', 'in-person')
        symptoms = request.form.get('symptoms', '')
        try:
            apt_date = datetime.strptime(apt_date_str, '%Y-%m-%d').date()
            if apt_date < date.today():
                flash('Please select a future date.', 'error')
                return render_template('appointment.html', services=services)
        except:
            flash('Invalid date.', 'error')
            return render_template('appointment.html', services=services)
        try:
            apt_time = datetime.strptime(apt_time_str, '%H:%M').time()
        except:
            flash('Invalid time.', 'error')
            return render_template('appointment.html', services=services)
        apt = Appointment(
            appointment_code=gen_code(),
            appointment_date=apt_date,
            appointment_time=apt_time,
            service_id=service_id,
            appointment_type=apt_type,
            symptoms=symptoms,
            status='pending',
            fee=200.0
        )
        if current_user.is_authenticated and current_user.patient_profile:
            apt.user_id = current_user.id
            apt.patient_id = current_user.patient_profile.id
        else:
            name = request.form.get('guest_name', '').strip()
            email = request.form.get('guest_email', '').strip()
            phone = request.form.get('guest_phone', '').strip()
            age = request.form.get('guest_age', type=int)
            if not all([name, email, phone]):
                flash('Name, email and phone are required.', 'error')
                return render_template('appointment.html', services=services)
            apt.guest_name = name
            apt.guest_email = email
            apt.guest_phone = phone
            apt.guest_age = age
        db.session.add(apt)
        db.session.commit()
        notif = Notification(
            appointment_id=apt.id,
            patient_id=apt.patient_id,
            type='whatsapp',
            message_type='confirmation',
            message=f'Hello, your appointment (Code: {apt.appointment_code}) at MediDent on {apt_date.strftime("%d %b %Y")} at {apt_time_str} is received. We will confirm shortly.',
            status='pending'
        )
        db.session.add(notif)
        db.session.commit()
        flash(f'Appointment booked! Code: {apt.appointment_code}', 'success')
        return redirect(url_for('appointments.confirmation', code=apt.appointment_code))
    return render_template('appointment.html', services=services)

@appointments_bp.route('/confirmation/<code>')
def confirmation(code):
    apt = Appointment.query.filter_by(appointment_code=code).first_or_404()
    return render_template('appointment_confirmation.html', appointment=apt)

@appointments_bp.route('/track')
def track():
    code = request.args.get('code', '')
    apt = None
    if code:
        apt = Appointment.query.filter_by(appointment_code=code.upper()).first()
        if not apt:
            flash('Appointment not found.', 'error')
    return render_template('appointment_track.html', appointment=apt, code=code)

@appointments_bp.route('/available-slots')
def available_slots():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'slots': []})
    try:
        apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return jsonify({'slots': []})
    all_slots = [f'{h:02d}:{m:02d}' for h in range(9, 19) for m in [0, 30]]
    booked = [str(a.appointment_time)[:5] for a in
              Appointment.query.filter_by(appointment_date=apt_date).filter(
                  Appointment.status.in_(['pending', 'confirmed'])).all()]
    available = [s for s in all_slots if s not in booked]
    return jsonify({'slots': available, 'booked': booked})
