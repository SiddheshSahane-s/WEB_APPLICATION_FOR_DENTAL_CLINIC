from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from CLINIC.models import db, Patient, Appointment, Prescription, MedicalReport, Invoice, User
import os

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def patient_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['patient', 'admin']:
            flash('Access denied.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    patient = current_user.patient_profile
    if not patient:
        flash('Patient profile not found.', 'error')
        return redirect(url_for('public.index'))
    upcoming = Appointment.query.filter_by(patient_id=patient.id).filter(
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date.asc()).limit(5).all()
    past = Appointment.query.filter_by(patient_id=patient.id).filter(
        Appointment.status == 'completed'
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient.id).order_by(Prescription.created_at.desc()).limit(5).all()
    reports = MedicalReport.query.filter_by(patient_id=patient.id).order_by(MedicalReport.created_at.desc()).limit(5).all()
    invoices = Invoice.query.filter_by(patient_id=patient.id).order_by(Invoice.created_at.desc()).limit(5).all()
    return render_template('patient/dashboard.html', patient=patient,
                           upcoming=upcoming, past=past,
                           prescriptions=prescriptions, reports=reports, invoices=invoices)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def profile():
    patient = current_user.patient_profile
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        if patient:
            patient.address = request.form.get('address', patient.address)
            patient.city = request.form.get('city', patient.city)
            patient.blood_group = request.form.get('blood_group', patient.blood_group)
            patient.allergies = request.form.get('allergies', patient.allergies)
            patient.medical_history = request.form.get('medical_history', patient.medical_history)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    return render_template('patient/profile.html', patient=patient)

@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    patient = current_user.patient_profile
    all_appointments = Appointment.query.filter_by(patient_id=patient.id)\
        .order_by(Appointment.appointment_date.desc()).all()
    return render_template('patient/appointments.html', appointments=all_appointments)

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    patient = current_user.patient_profile
    all_prescriptions = Prescription.query.filter_by(patient_id=patient.id)\
        .order_by(Prescription.created_at.desc()).all()
    return render_template('patient/prescriptions.html', prescriptions=all_prescriptions)

@patient_bp.route('/reports')
@login_required
@patient_required
def reports():
    patient = current_user.patient_profile
    all_reports = MedicalReport.query.filter_by(patient_id=patient.id)\
        .order_by(MedicalReport.created_at.desc()).all()
    return render_template('patient/reports.html', reports=all_reports)

@patient_bp.route('/billing')
@login_required
@patient_required
def billing():
    patient = current_user.patient_profile
    all_invoices = Invoice.query.filter_by(patient_id=patient.id)\
        .order_by(Invoice.created_at.desc()).all()
    return render_template('patient/billing.html', invoices=all_invoices)
