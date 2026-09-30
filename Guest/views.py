from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password

from .models import tbl_registration


# =========================
# HOME PAGE
# =========================
def HomePage(request):
    return render(request, "Guest/HomePage.html")


# =========================
# USER REGISTRATION
# =========================
def UserRegistration(request):

    if request.method == "POST":

        name = request.POST.get("txt_name", "").strip()
        email = request.POST.get("txt_email", "").strip().lower()
        contact = request.POST.get("txt_contact", "").strip()
        address = request.POST.get("txt_Address", "").strip()
        password = request.POST.get("txt_password", "").strip()

        # Check required fields
        if not name or not email or not contact or not password:
            return render(
                request,
                "Guest/UserRegistration.html",
                {
                    "error": "Please fill all required fields."
                }
            )

        # Check email already exists
        if tbl_registration.objects.filter(
            user_email=email
        ).exists():

            return render(
                request,
                "Guest/UserRegistration.html",
                {
                    "error": "Email already registered!"
                }
            )

        # Create user
        tbl_registration.objects.create(
            user_name=name,
            user_email=email,
            user_contact=contact,
            user_address=address,
            user_password=make_password(password),
            role="USER",
            is_active=True
        )

        # Registration successful → Login
        return redirect("Guest:Login")

    return render(
        request,
        "Guest/UserRegistration.html"
    )


# =========================
# USER / COMMON LOGIN
# =========================
def Login(request):

    if request.method == "POST":

        email = request.POST.get(
            "txt_email", ""
        ).strip().lower()

        password = request.POST.get(
            "txt_password", ""
        ).strip()

        try:

            user = tbl_registration.objects.get(
                user_email=email,
                is_active=True
            )

            # Check encrypted password
            if check_password(
                password,
                user.user_password
            ):

                # Create session
                request.session["user_id"] = user.id
                request.session["user_name"] = user.user_name
                request.session["user_email"] = user.user_email
                request.session["role"] = user.role

                # USER
                if user.role == "USER":
                    return redirect(
                        "User:UserDashboard"
                    )

                # DOCTOR
                elif user.role == "DOCTOR":
                    return redirect(
                        "Doctor:DoctorDashboard"
                    )

                # ADMIN
                elif user.role == "ADMIN":
                    return redirect(
                        "Administrator:AdminDashboard"
                    )

                else:
                    return render(
                        request,
                        "Guest/Login.html",
                        {
                            "error": "Invalid user role!"
                        }
                    )

            else:

                return render(
                    request,
                    "Guest/Login.html",
                    {
                        "error": "Incorrect password!"
                    }
                )

        except tbl_registration.DoesNotExist:

            return render(
                request,
                "Guest/Login.html",
                {
                    "error": "Email not registered!"
                }
            )

    return render(
        request,
        "Guest/Login.html"
    )


# =========================
# ADMIN LOGIN
# =========================
def AdminLogin(request):

    if request.method == "POST":

        email = request.POST.get(
            "txt_email", ""
        ).strip().lower()

        password = request.POST.get(
            "txt_password", ""
        ).strip()

        # Default Admin Login
        if email == "admin@gmail.com" and password == "admin123":

            request.session["user_id"] = 0
            request.session["user_name"] = "Administrator"
            request.session["user_email"] = email
            request.session["role"] = "ADMIN"

            return redirect(
                "Administrator:AdminDashboard"
            )

        return render(
            request,
            "Guest/AdminLogin.html",
            {
                "error": "Invalid admin email or password"
            }
        )

    return render(
        request,
        "Guest/AdminLogin.html"
    )


# =========================
# DOCTOR LOGIN
# =========================
def DoctorLogin(request):

    if request.method == "POST":

        email = request.POST.get(
            "txt_email", ""
        ).strip().lower()

        password = request.POST.get(
            "txt_password", ""
        ).strip()

        try:

            # Find doctor from database
            doctor = tbl_registration.objects.get(
                user_email=email,
                is_active=True,
                role="DOCTOR"
            )

            # Check encrypted password
            if check_password(
                password,
                doctor.user_password
            ):

                # Create doctor session
                request.session["user_id"] = doctor.id
                request.session["user_name"] = doctor.user_name
                request.session["user_email"] = doctor.user_email
                request.session["role"] = "DOCTOR"

                return redirect(
                    "Doctor:DoctorDashboard"
                )

            return render(
                request,
                "Guest/DoctorLogin.html",
                {
                    "error": "Incorrect password!"
                }
            )

        except tbl_registration.DoesNotExist:

            return render(
                request,
                "Guest/DoctorLogin.html",
                {
                    "error": "Doctor email not registered!"
                }
            )

    return render(
        request,
        "Guest/DoctorLogin.html"
    )


# =========================
# LOGOUT
# =========================
def Logout(request):

    request.session.flush()

    return redirect(
        "Guest:HomePage"
    )