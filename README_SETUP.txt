PREGNANCY & BABY TRACKER - FIXED VERSION

1. Open terminal in this folder.
2. Create/activate a Python 3.10+ virtual environment.
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py seed_project
6. python manage.py runserver
7. Open http://127.0.0.1:8000/

DEMO LOGIN
Admin: admin123@gmail.com / admin123
Doctor: doctor123@gmail.com / doctor123

USER REGISTRATION
Register a normal user from User Registration. Passwords are stored hashed and the same shared tbl_registration table is used by User, Doctor and Admin.

IMPORTANT
The supplied old project had separate registration models in Guest and Administrator, plain-password login, an undefined admin_guard, missing Doctor templates, incorrect template directory names, and several form/url mismatches. This version keeps the existing module structure but connects them to the single Guest.tbl_registration model.
