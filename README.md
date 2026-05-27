# MediDent Multispeciality Dental Clinic

A premium, modern dental clinic management website and web application built with Python, Flask, SQLAlchemy, and Vanilla JS/CSS.

## Features Included
- **Public Website:** Home, About, Specialities, Services, Blog, Contact
- **Patient Portal:** Dashboard, Appointments, Prescriptions, Medical Reports, Billing
- **Authentication:** Role-based (Patient, Admin, Dentist, Receptionist)
- **Admin Panel:** Complete management of patients, appointments, billing, blog, and users.
- **WhatsApp Reminders:** Integrated architecture for sending WhatsApp notifications via Twilio API.
- **Database:** SQLite with SQLAlchemy ORM and sample seeded data.

## Setup Instructions

1. **Activate Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```powershell
   python app.py
   ```
   *Note: On the first run, the database (`database/mediDent.db`) will be automatically created and seeded with dummy data.*

4. **Access the Application:**
   Open your browser and navigate to `http://localhost:5000`

## Demo Accounts (Passwords: Role@123)
- **Admin Panel:** `admin@medident.in` / `Admin@123`
- **Doctor:** `dr.abhik@medident.in` / `Doctor@123`
- **Patient:** `patient@medident.in` / `Patient@123`

## Twilio WhatsApp Setup (Optional)
To enable WhatsApp notifications, create a `.env` file in the root directory and add your Twilio credentials:
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```
