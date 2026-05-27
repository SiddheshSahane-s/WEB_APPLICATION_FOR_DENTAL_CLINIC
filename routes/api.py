from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from CLINIC.models import db, Appointment, Notification, Patient
from datetime import datetime
import requests as http_requests

api_bp = Blueprint('api', __name__, url_prefix='/api')

def send_whatsapp_reminder(apt):
    """Send WhatsApp reminder via Twilio or queue it."""
    phone = None
    name = apt.guest_name or 'Patient'
    if apt.patient and apt.patient.user:
        phone = apt.patient.user.phone
        name = apt.patient.user.name
    elif apt.guest_phone:
        phone = apt.guest_phone

    apt_date = apt.appointment_date.strftime('%d %b %Y') if apt.appointment_date else 'N/A'
    apt_time = str(apt.appointment_time)[:5] if apt.appointment_time else 'N/A'

    message = (
        f"Hello {name}, this is a reminder for your appointment with "
        f"Dr. Abhik Ray at MediDent Multispeciality Dental Clinic on "
        f"{apt_date} at {apt_time}. "
        f"Appointment Code: {apt.appointment_code}. "
        f"For queries call: +91-98765-43210."
    )

    notif = Notification(
        appointment_id=apt.id,
        patient_id=apt.patient_id,
        type='whatsapp',
        message_type='reminder',
        message=message,
        status='pending'
    )

    # Try Twilio if configured
    from CLINIC.models import SystemSetting
    
    def get_setting(key, fallback=None):
        setting = SystemSetting.query.filter_by(key=key).first()
        return setting.value if setting and setting.value else current_app.config.get(key, fallback)
        
    twilio_sid = get_setting('TWILIO_ACCOUNT_SID')
    twilio_token = get_setting('TWILIO_AUTH_TOKEN')
    twilio_from = get_setting('TWILIO_WHATSAPP_FROM')

    if twilio_sid and twilio_token and phone:
        try:
            url = f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json'
            data = {
                'From': twilio_from,
                'To': f'whatsapp:+91{phone.replace("+91","").replace(" ","")}',
                'Body': message
            }
            resp = http_requests.post(url, data=data, auth=(twilio_sid, twilio_token), timeout=10)
            if resp.status_code == 201:
                notif.status = 'sent'
                notif.sent_at = datetime.utcnow()
                db.session.add(notif)
                db.session.commit()
                return True
        except Exception as e:
            notif.status = 'failed'
            notif.error_message = str(e)

    db.session.add(notif)
    db.session.commit()
    return False

@api_bp.route('/appointments/check', methods=['GET'])
def check_appointment():
    code = request.args.get('code', '').upper()
    if not code:
        return jsonify({'error': 'Code required'}), 400
    apt = Appointment.query.filter_by(appointment_code=code).first()
    if not apt:
        return jsonify({'found': False}), 404
    return jsonify({
        'found': True,
        'code': apt.appointment_code,
        'status': apt.status,
        'date': str(apt.appointment_date),
        'time': str(apt.appointment_time)[:5],
        'service': apt.service.name if apt.service else 'General Consultation'
    })

@api_bp.route('/services', methods=['GET'])
def list_services():
    from CLINIC.models import Service
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([{'id': s.id, 'name': s.name, 'duration': s.duration_minutes, 'price': s.base_price} for s in services])
