# Pregnancy & Baby Tracker — Connected Django Project

## Main database flow
Registration/Login -> Role -> Dashboard -> Profile -> Pregnancy -> Weekly Records -> Baby -> Appointments -> Doctor -> Admin -> Reports/Messages -> AI/ML.

## Run in VS Code (Windows)
```cmd
cd "Pregnancy & Baby Tracker"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Database
SQLite database: `db.sqlite3`.
All application roles use `tbl_registration` with roles USER, DOCTOR and ADMIN.

## Default administrator
The Admin Login page creates the first admin account if no ADMIN exists:
- Email: admin@gmail.com
- Password: admin123

Change the password for any real deployment.

## ML
The maternal risk model is loaded from:
- `Dataset/maternal_risk_model.pkl`
- `Dataset/risk_label_encoder.pkl`

Admin can upload a compatible CSV from Upload Dataset to retrain the Random Forest model.

## Important model relationships
- UserProfile -> tbl_registration (OneToOne)
- PregnancyTracker -> tbl_registration (ForeignKey)
- PregnancyWeeklyRecord -> PregnancyTracker (ForeignKey)
- Baby -> tbl_registration (ForeignKey)
- BabyGrowth -> Baby (ForeignKey)
- Doctor -> tbl_registration (OneToOne)
- Appointment -> User + Doctor
- Prescription -> User + Doctor
- Message -> registration sender/receiver
- MedicalReport -> User + optional Doctor
- Nutrition/Medicine/Milestone/Dataset -> Admin-managed tables
