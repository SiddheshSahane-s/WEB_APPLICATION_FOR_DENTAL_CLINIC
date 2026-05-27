from app import create_app, seed_database
from models import db

app = create_app('production')

# Create tables if they don't exist in production (e.g., when connecting to a new PostgreSQL DB)
with app.app_context():
    db.create_all()
    # You can also call seed_database(app) here if you want default admin/data on a fresh database
    try:
        from models import User
        if not User.query.first():
            seed_database(app)
    except Exception as e:
        print(f"Skipping seeding: {e}")

if __name__ == '__main__':
    app.run()
