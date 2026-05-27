import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db, User
from config import config

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

    # Extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.patient import patient_bp
    from routes.admin import admin_bp
    from routes.appointments import appointments_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(api_bp)

    # Inject clinic config into all templates
    @app.context_processor
    def inject_globals():
        return {
            'CLINIC_NAME': app.config['CLINIC_NAME'],
            'DOCTOR_NAME': app.config['DOCTOR_NAME'],
            'CONSULTATION_FEE': app.config['CONSULTATION_FEE'],
            'CLINIC_PHONE': app.config['CLINIC_PHONE'],
            'CLINIC_EMAIL': app.config['CLINIC_EMAIL'],
            'CLINIC_ADDRESS': app.config['CLINIC_ADDRESS'],
            'WHATSAPP_NUMBER': app.config['WHATSAPP_NUMBER'],
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app


def seed_database(app):
    """Seed with sample data."""
    with app.app_context():
        from models import User, Patient, Service, Speciality, Testimonial, BlogPost
        from datetime import date
        import random, string, json

        # Admin user
        if not User.query.filter_by(email='admin@medident.in').first():
            admin = User(name='Admin', email='admin@medident.in', phone='9000000000', role='admin')
            admin.set_password('Admin@123')
            db.session.add(admin)

        # Doctor user
        if not User.query.filter_by(email='dr.abhik@medident.in').first():
            doc = User(name='Dr. Abhik Ray', email='dr.abhik@medident.in', phone='9876543210', role='dentist')
            doc.set_password('Doctor@123')
            db.session.add(doc)

        # Demo patient
        if not User.query.filter_by(email='patient@medident.in').first():
            pu = User(name='Rahul Sharma', email='patient@medident.in', phone='9123456789', role='patient')
            pu.set_password('Patient@123')
            db.session.add(pu)
            db.session.flush()
            pp = Patient(user_id=pu.id, patient_code='MD000001', age=32, gender='Male',
                        blood_group='O+', city='Kolkata', allergies='None',
                        medical_history='Mild hypertension', dental_history='Root canal done in 2022')
            db.session.add(pp)

        # Services
        service_data = [
            ('General Consultation', 'Comprehensive dental check-up', 30, 200, 'consultation', 'fa-stethoscope'),
            ('Root Canal Treatment', 'Complete RCT procedure', 90, 3500, 'treatment', 'fa-tooth'),
            ('Teeth Whitening', 'Professional whitening', 60, 2500, 'cosmetic', 'fa-star'),
            ('Dental Implants', 'Permanent tooth replacement', 120, 25000, 'implant', 'fa-circle-dot'),
            ('Braces & Orthodontics', 'Teeth alignment', 60, 15000, 'orthodontics', 'fa-grip-lines'),
            ('Dental Cleaning', 'Scaling and polishing', 45, 800, 'cleaning', 'fa-shield'),
            ('Tooth Extraction', 'Simple/surgical extraction', 45, 500, 'extraction', 'fa-minus-circle'),
            ('Smile Designing', 'Complete smile makeover', 90, 20000, 'cosmetic', 'fa-smile'),
            ('X-Ray Services', 'Digital dental X-Ray', 15, 300, 'diagnostic', 'fa-radiation'),
            ('Emergency Dental Care', '24hr emergency care', 60, 500, 'emergency', 'fa-ambulance'),
            ('Pediatric Dentistry', 'Children dental care', 45, 400, 'pediatric', 'fa-child'),
            ('Gum Treatment', 'Periodontal treatment', 60, 1500, 'periodontal', 'fa-leaf'),
        ]
        for name, desc, dur, price, cat, icon in service_data:
            if not Service.query.filter_by(name=name).first():
                db.session.add(Service(name=name, description=desc, duration_minutes=dur,
                                      base_price=price, category=cat, icon=icon))

        # Specialities
        spec_data = [
            ('General Dentistry', 'general-dentistry', 'Comprehensive dental care for the whole family including check-ups, cleanings, and preventive treatments.',
             'Toothache, Sensitivity, Bleeding gums, Bad breath', 'Examination, Cleaning, Fillings, Fluoride treatment, Sealants',
             'How often should I visit? Every 6 months.', 'fa-tooth'),
            ('Root Canal Treatment', 'root-canal-treatment', 'Modern painless root canal therapy to save infected teeth and relieve severe pain.',
             'Severe toothache, Prolonged sensitivity, Swelling, Darkening of tooth', 'RCT, Crown placement, Pain management',
             'Is RCT painful? No, done under local anesthesia.', 'fa-circle-half-stroke'),
            ('Teeth Whitening', 'teeth-whitening', 'Professional teeth whitening for a brighter, more confident smile.',
             'Stained teeth, Yellow discoloration, Coffee/tea stains', 'Laser whitening, Bleaching, Custom trays',
             'How long does whitening last? 1-2 years with care.', 'fa-star'),
            ('Dental Implants', 'dental-implants', 'Permanent, natural-looking tooth replacement with titanium implants.',
             'Missing teeth, Ill-fitting dentures, Jawbone loss', 'Implant placement, Abutment, Crown fitting',
             'How long do implants last? Lifetime with proper care.', 'fa-circle-dot'),
            ('Braces & Orthodontics', 'braces-orthodontics', 'Straighten teeth and correct bite issues for a perfect smile.',
             'Crooked teeth, Overcrowding, Overbite, Underbite', 'Metal braces, Clear aligners, Retainers',
             'At what age should orthodontics start? Best 10-14 years, but any age works.', 'fa-grip-lines'),
            ('Cosmetic Dentistry', 'cosmetic-dentistry', 'Smile makeover treatments to enhance your appearance and confidence.',
             'Chipped teeth, Gaps, Discoloration, Uneven smile', 'Veneers, Bonding, Contouring, Smile design',
             'What is smile designing? Custom treatment to create your perfect smile.', 'fa-smile'),
            ('Pediatric Dentistry', 'pediatric-dentistry', 'Gentle, child-friendly dental care for babies, children and teens.',
             'Tooth decay, Thumb sucking, Delayed eruption', 'Preventive care, Fluoride, Sealants, Space maintainers',
             'When should a child first visit? By age 1 or first tooth.', 'fa-child'),
            ('Gum Treatment', 'gum-treatment', 'Diagnosis and treatment of gum disease to preserve your natural teeth.',
             'Bleeding gums, Gum recession, Loose teeth, Bad breath', 'Scaling, Root planing, Surgery if needed',
             'Can gum disease be cured? Early stages yes, advanced managed.', 'fa-leaf'),
        ]
        for name, slug, desc, symptoms, treatments, faq, icon in spec_data:
            if not Speciality.query.filter_by(slug=slug).first():
                db.session.add(Speciality(name=name, slug=slug, description=desc,
                                         symptoms=symptoms, treatment_methods=treatments,
                                         faq=faq, icon=icon))

        # Testimonials
        testimonial_data = [
            ('Priya Mehta', 5, 'Dr. Abhik Ray is exceptional! My root canal was completely painless. The clinic is very modern and clean.', 'Root Canal Treatment'),
            ('Rajesh Kumar', 5, 'Best dental experience ever! Teeth whitening results are amazing. Highly recommended!', 'Teeth Whitening'),
            ('Sneha Patel', 5, 'Got my braces done here. The team is friendly and professional. My smile transformed!', 'Braces'),
            ('Amit Ghosh', 5, 'Dental implant procedure was smooth. Dr. Ray explained everything clearly. Worth every rupee.', 'Dental Implants'),
            ('Kavya Sharma', 5, 'My daughter loves coming here! The pediatric dentist is so gentle and patient with kids.', 'Pediatric Dentistry'),
            ('Mohammed Rafiq', 4, 'Great clinic with modern equipment. Online appointment booking is very convenient.', 'General Consultation'),
        ]
        for name, rating, msg, treatment in testimonial_data:
            if not Testimonial.query.filter_by(patient_name=name).first():
                db.session.add(Testimonial(patient_name=name, rating=rating, message=msg, treatment=treatment, is_approved=True))

        # Sample blog posts
        blog_data = [
            ('10 Tips for Healthy Teeth and Gums', '10-tips-healthy-teeth', 'Essential dental hygiene tips',
             '''<h2>1. Brush Twice Daily</h2><p>Use fluoride toothpaste and a soft-bristle brush...</p>
             <h2>2. Floss Daily</h2><p>Flossing removes plaque between teeth...</p>
             <h2>3. Use Mouthwash</h2><p>Antiseptic mouthwash kills bacteria...</p>
             <h2>4. Limit Sugar</h2><p>Sugar feeds bacteria that cause cavities...</p>
             <h2>5. Visit Your Dentist Regularly</h2><p>Every 6 months for check-up and cleaning...</p>''',
             'Dental Tips', 'teeth, hygiene, health, tips'),
            ('Understanding Root Canal Treatment', 'understanding-root-canal', 'Complete guide to RCT',
             '''<h2>What is Root Canal?</h2><p>Root canal treatment (RCT) saves an infected tooth...</p>
             <h2>When is it Needed?</h2><p>When decay reaches the tooth pulp...</p>
             <h2>The Procedure</h2><p>Step 1: X-ray, Step 2: Anesthesia, Step 3: Cleaning...</p>''',
             'Treatment Guide', 'root canal, RCT, dental treatment'),
            ('Dental Implants vs Dentures: Which is Right for You?', 'implants-vs-dentures', 'Comparison guide',
             '''<h2>Dental Implants</h2><p>Permanent, natural-looking, titanium-based...</p>
             <h2>Dentures</h2><p>Removable, affordable, traditional option...</p>
             <h2>Which to Choose?</h2><p>Depends on bone density, budget, lifestyle...</p>''',
             'Patient Education', 'implants, dentures, tooth replacement'),
        ]
        from datetime import datetime
        for title, slug, excerpt, content, category, tags in blog_data:
            if not BlogPost.query.filter_by(slug=slug).first():
                admin_user = User.query.filter_by(role='admin').first()
                db.session.add(BlogPost(
                    title=title, slug=slug, excerpt=excerpt, content=content,
                    category=category, tags=tags,
                    author_id=admin_user.id if admin_user else None,
                    is_published=True, published_at=datetime.utcnow()
                ))

        db.session.commit()
        print('[OK] Database seeded successfully.')


if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        db.create_all()
        seed_database(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
