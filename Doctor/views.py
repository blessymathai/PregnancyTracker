from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from Guest.models import tbl_registration
from User.models import (
    tbl_UserProfile,
    tbl_PregnancyTracker,
    tbl_Baby,
)
from .models import (
    tbl_Doctor,
    tbl_Appointment,
    tbl_Prescription,
    tbl_Message,
)

# =========================================================
# DOCTOR LOGIN USER
# =========================================================

def doctor_user(request):

    uid = request.session.get('user_id')

    if not uid or request.session.get('role') != 'DOCTOR':
        return None

    return tbl_registration.objects.filter(
        id=uid,
        is_active=True,
        role='DOCTOR'
    ).first()


# =========================================================
# DOCTOR LOGIN GUARD
# =========================================================

def guard(request):

    user = doctor_user(request)

    if user:
        return user, None

    return None, redirect('Guest:Login')


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

def DoctorDashboard(request):

    user, response = guard(request)

    if response:
        return response

    doctor = get_object_or_404(
        tbl_Doctor,
        user=user
    )

    # Store doctor name in session
    request.session['doctor_name'] = doctor.name

    # Current date
    today = timezone.localdate()

    # Doctor appointments
    appointments = doctor.appointments.select_related(
        'patient'
    )

    # -----------------------------------------------------
    # TODAY'S APPOINTMENTS
    # IMPORTANT:
    # Model field = appointment_date
    # -----------------------------------------------------

    today_appointments = appointments.filter(
        appointment_date=today
    ).count()

    # -----------------------------------------------------
    # RECENT 5 APPOINTMENTS
    # IMPORTANT:
    # Model fields = appointment_date, appointment_time
    # -----------------------------------------------------

    recent_appointments = appointments.order_by(
        '-appointment_date',
        '-appointment_time'
    )[:5]

    # -----------------------------------------------------
    # DASHBOARD DATA
    # -----------------------------------------------------

    context = {

        'doctor': doctor,

        # Total registered active users
        'total_patients': tbl_registration.objects.filter(
            role='USER',
            is_active=True
        ).count(),

        # Today's appointments
        'today_appointments': today_appointments,

        # Pregnancy records
        'pregnancy_records': tbl_PregnancyTracker.objects.count(),

        # Baby records
        'baby_records': tbl_Baby.objects.count(),

        # Recent appointments
        'recent_appointments': recent_appointments,
    }

    return render(
        request,
        'Doctor/DoctorDashboard.html',
        context
    )


# =========================================================
# PATIENTS
# =========================================================

def Patients(request):
    # Display all registered user/patient profiles
    patients = tbl_UserProfile.objects.select_related("user").all()

    return render(
        request,
        "Doctor/Patients.html",
        {
            "patients": patients
        }
    )


def PatientDetails(request, patient_id):
    # Display one selected patient
    patient = get_object_or_404(
        tbl_UserProfile.objects.select_related("user"),
        id=patient_id
    )

    return render(
        request,
        "Doctor/Patient.html",
        {
            "patient": patient
        }
    )



# =========================================================
# APPOINTMENTS
# =========================================================

def Appointments(request):

    doctor_user_id = request.session.get('user_id')

    doctor = get_object_or_404(
        tbl_Doctor,
        user_id=doctor_user_id
    )

    appointments = tbl_Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        'patient'
    ).order_by(
        '-appointment_date',
        '-appointment_time'
    )

    return render(
        request,
        'Doctor/Appointments.html',
        {
            'Appointments': appointments
        }
    )
    # -----------------------------------------------------
    # UPDATE APPOINTMENT STATUS
    # -----------------------------------------------------

    if request.method == 'POST':

        appointment_id = request.POST.get(
            'appointment_id'
        )

        status = request.POST.get(
            'status'
        )

        appointment = get_object_or_404(
            tbl_Appointment,
            id=appointment_id,
            doctor=doctor
        )

        if status in [
            'Pending',
            'Approved',
            'Rejected',
            'Completed'
        ]:

            appointment.status = status

            appointment.save(
                update_fields=['status']
            )

            messages.success(
                request,
                f'Appointment {status.lower()} successfully.'
            )

        return redirect(
            'Doctor:Appointments'
        )

    # -----------------------------------------------------
    # DISPLAY APPOINTMENTS
    # -----------------------------------------------------

    appointments = tbl_Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        'patient'
    ).order_by(
        '-appointment_date',
        '-appointment_time'
    )

    return render(
        request,
        'Doctor/Appointments.html',
        {
            'doctor': doctor,
            'appointments': appointments
        }
    )

    # -----------------------------------------------------
    # UPDATE APPOINTMENT
    # -----------------------------------------------------

    if request.method == 'POST':

        appointment_id = request.POST.get(
            'appointment'
        )

        appointment = get_object_or_404(
            tbl_Appointment,
            id=appointment_id,
            doctor=doctor
        )

        appointment.status = request.POST.get(
            'status',
            appointment.status
        )

        appointment.notes = request.POST.get(
            'notes',
            appointment.notes
        )

        appointment.save()

        messages.success(
            request,
            'Appointment updated successfully.'
        )

        return redirect(
            'Doctor:Appointments'
        )

    # -----------------------------------------------------
    # GET APPOINTMENTS
    # -----------------------------------------------------

    appointments = doctor.appointments.select_related(
        'patient'
    ).order_by(
        '-appointment_date',
        '-appointment_time'
    )

    return render(
        request,
        'Doctor/Appointments.html',
        {
            'doctor': doctor,
            'appointments': appointments
        }
    )

def AcceptAppointment(request, appointment_id):
    appointment = get_object_or_404(
        tbl_Appointment,
        id=appointment_id
    )

    appointment.status = 'Approved'
    appointment.save()

    messages.success(
        request,
        f'Appointment for {appointment.patient.user_name} confirmed successfully! Patient can now message you.'
    )

    return redirect('Doctor:Appointments')


def RejectAppointment(request, appointment_id):
    appointment = get_object_or_404(
        tbl_Appointment,
        id=appointment_id
    )

    appointment.status = 'Rejected'
    appointment.save()

    messages.warning(
        request,
        f'Appointment for {appointment.patient.user_name} rejected.'
    )

    return redirect('Doctor:Appointments')

# =========================================================
# PREGNANCY RECORDS
# =========================================================

def PregnancyRecords(request):

    if request.method == "POST":

        mother = request.POST.get("mother")
        last_period_date = request.POST.get("last_period_date")
        expected_delivery_date = request.POST.get("expected_delivery_date")
        current_week = request.POST.get("current_week")
        weight = request.POST.get("weight")
        symptoms = request.POST.get("symptoms")

        tbl_PregnancyTracker.objects.create(
            mother=mother,
            last_period_date=last_period_date,
            expected_delivery_date=expected_delivery_date,
            current_week=current_week,
            weight=weight,
            symptoms=symptoms
        )

        messages.success(
            request,
            "Pregnancy record added successfully."
        )

        return redirect("Doctor:PregnancyRecords")

    pregnancy_records = tbl_PregnancyTracker.objects.all().order_by("-id")

    return render(
        request,
        "Doctor/PregnancyRecords.html",
        {
            "pregnancy_records": pregnancy_records
        }
    )


# =========================================================
# BABY RECORDS
# =========================================================

def BabyRecords(request):

    # ==========================
    # ADD BABY RECORD
    # ==========================

    if request.method == "POST":

        mother_name = request.POST.get("mother")
        week = request.POST.get("week")
        time = request.POST.get("time")
        date = request.POST.get("date_of_birth")
        weight = request.POST.get("weight")

        # Find registered mother
        try:

            mother = tbl_registration.objects.get(
                user_name=mother_name,
                role="USER"
            )

        except tbl_registration.DoesNotExist:

            messages.error(
                request,
                "Mother not found. Please enter a registered mother name."
            )

            return redirect("Doctor:BabyRecords")

        # Save baby record
        tbl_Baby.objects.create(
            user=mother,
            week=week,
            time=time,
            date=date,
            weight=weight
        )

        messages.success(
            request,
            "Baby record added successfully."
        )

        return redirect("Doctor:BabyRecords")


    # ==========================
    # DISPLAY BABY RECORDS
    # ==========================

    baby_records = tbl_Baby.objects.select_related(
        "user"
    ).all().order_by("-id")

    total_babies = baby_records.count()


    context = {
        "baby_records": baby_records,
        "total_babies": total_babies,
    }


    return render(
        request,
        "Doctor/BabyRecords.html",
        context
    )


# =========================================================
# PRESCRIPTIONS
# =========================================================

def Prescriptions(request):

    user, response = guard(request)

    if response:
        return response

    doctor = get_object_or_404(
        tbl_Doctor,
        user=user
    )

    patients = tbl_registration.objects.filter(
        role='USER',
        is_active=True
    )

    # -----------------------------------------------------
    # CREATE PRESCRIPTION
    # -----------------------------------------------------

    if request.method == 'POST':

        patient_id = request.POST.get(
            'patient'
        )

        medicine = request.POST.get(
            'medicine',
            ''
        )

        dosage = request.POST.get(
            'dosage',
            ''
        )

        duration = request.POST.get(
            'duration',
            ''
        )

        instructions = request.POST.get(
            'instructions',
            ''
        )

        patient = get_object_or_404(
            tbl_registration,
            id=patient_id,
            role='USER'
        )

        tbl_Prescription.objects.create(

            patient=patient,

            doctor=doctor,

            medicine=medicine,

            dosage=dosage,

            duration=duration,

            instructions=instructions
        )

        messages.success(
            request,
            'Prescription saved successfully.'
        )

        return redirect(
            'Doctor:Prescriptions'
        )

    # -----------------------------------------------------
    # GET PRESCRIPTIONS
    # -----------------------------------------------------

    prescriptions = doctor.prescriptions.select_related(
        'patient'
    )

    return render(
        request,
        'Doctor/Prescriptions.html',
        {
            'doctor': doctor,
            'patients': patients,
            'prescriptions': prescriptions
        }
    )


# =========================================================
# MESSAGES
# =========================================================

def Messages(request):
    user, response = guard(request)
    if response:
        return response

    doctor = get_object_or_404(tbl_Doctor, user=user)

    # STRICT REQUIREMENT: Only patients with CONFIRMED ('Approved') appointments with this doctor
    confirmed_appointments = tbl_Appointment.objects.filter(
        doctor=doctor,
        status='Approved'
    ).select_related('patient').order_by('-appointment_date')

    confirmed_patient_ids = confirmed_appointments.values_list('patient_id', flat=True).distinct()
    confirmed_patients = tbl_registration.objects.filter(id__in=confirmed_patient_ids)

    # Selected patient (from ?patient=<id> or POST)
    selected_patient_id = request.GET.get('patient') or request.POST.get('patient') or request.POST.get('patient_id')
    try:
        selected_patient_id = int(selected_patient_id) if selected_patient_id else None
    except (ValueError, TypeError):
        selected_patient_id = None

    if request.method == 'POST':
        patient_id = request.POST.get('patient') or request.POST.get('patient_id')
        text = request.POST.get('message', '').strip()

        if not patient_id:
            messages.error(request, 'Please select a confirmed patient to message.')
            return redirect('Doctor:Messages')

        patient = get_object_or_404(tbl_registration, id=patient_id, role='USER')

        # STRICT VALIDATION: Ensure this patient has an Approved appointment with this doctor
        has_approved = tbl_Appointment.objects.filter(
            doctor=doctor,
            patient=patient,
            status='Approved'
        ).exists()

        if not has_approved:
            messages.error(
                request,
                f'You can only chat with {patient.user_name} through a confirmed appointment.'
            )
            return redirect('Doctor:Messages')

        if not text:
            messages.error(request, 'Message cannot be empty.')
            return redirect(f"/Doctor/Messages/?patient={patient.id}")

        tbl_Message.objects.create(
            sender=user,
            receiver=patient,
            message=text
        )
        messages.success(request, f'Message sent to {patient.user_name}.')
        return redirect(f"/Doctor/Messages/?patient={patient.id}")

    # Messages involving doctor and confirmed patients
    msgs = tbl_Message.objects.filter(
        (Q(sender=user) & Q(receiver_id__in=confirmed_patient_ids)) |
        (Q(receiver=user) & Q(sender_id__in=confirmed_patient_ids))
    ).select_related('sender', 'receiver').order_by('sent_at')

    # Default to first confirmed patient if not selected
    if not selected_patient_id and confirmed_patients.exists():
        selected_patient_id = confirmed_patients.first().id

    active_patient = None
    if selected_patient_id:
        active_patient = confirmed_patients.filter(id=selected_patient_id).first()
        if active_patient:
            conversation = msgs.filter(
                Q(sender=active_patient) | Q(receiver=active_patient)
            )
        else:
            conversation = msgs
    else:
        conversation = msgs

    return render(
        request,
        'Doctor/Messages.html',
        {
            'doctor': doctor,
            'confirmed_patients': confirmed_patients,
            'patients': confirmed_patients,
            'messages_list': msgs,
            'conversation': conversation,
            'active_patient': active_patient,
            'selected_patient_id': selected_patient_id,
            'has_confirmed_patient': confirmed_patients.exists(),
        }
    )


# =========================================================
# DOCTOR AI CHAT BOX
# =========================================================

def ChatBox(request):

    user, response = guard(request)

    if response:
        return response

    doctor = get_object_or_404(
        tbl_Doctor,
        user=user
    )

    if request.method == 'POST':

        question = request.POST.get(
            'message',
            ''
        ).strip().lower()

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        if 'risk' in question:

            answer = (
                'Please review the patient pregnancy data '
                'and use the AI risk prediction module '
                'for the risk assessment.'
            )

        # -------------------------------------------------
        # NUTRITION
        # -------------------------------------------------

        elif 'nutrition' in question:

            answer = (
                'Nutrition recommendations can be '
                'generated using the nutrition dataset '
                'connected to the AI module.'
            )

        # -------------------------------------------------
        # APPOINTMENT
        # -------------------------------------------------

        elif 'appointment' in question:

            answer = (
                'You can view and manage patient '
                'appointments from the Appointments section.'
            )

        # -------------------------------------------------
        # PREGNANCY
        # -------------------------------------------------

        elif 'pregnancy' in question:

            answer = (
                'Pregnancy records and weekly tracking '
                'information are available in Pregnancy Records.'
            )

        # -------------------------------------------------
        # BABY
        # -------------------------------------------------

        elif 'baby' in question:

            answer = (
                'Baby growth and baby records can be '
                'viewed from the Baby Records section.'
            )

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        else:

            answer = (
                'Doctor AI Assistant: I can help with '
                'pregnancy tracking, appointments, '
                'nutrition, baby growth and general '
                'project information.'
            )

        # -------------------------------------------------
        # AJAX RESPONSE
        # -------------------------------------------------

        if request.headers.get(
            'x-requested-with'
        ) == 'XMLHttpRequest':

            return JsonResponse({
                'answer': answer
            })

    return render(
        request,
        'Doctor/ChatBox.html',
        {
            'doctor': doctor
        }
    )


# =========================================================
# DOCTOR LOGOUT
# =========================================================

def Logout(request):

    request.session.flush()

    return redirect(
        'Guest:HomePage'
    )


# =========================================================
# DOCTOR REGISTRATION
# =========================================================

def DoctorRegistrationView(request):

    if request.method == 'POST':

        # -------------------------------------------------
        # BASIC DETAILS
        # -------------------------------------------------

        name = request.POST.get(
            'txt_name',
            ''
        ).strip()

        email = request.POST.get(
            'txt_email',
            ''
        ).strip().lower()

        contact = request.POST.get(
            'txt_contact',
            ''
        ).strip()

        address = request.POST.get(
            'txt_address',
            ''
        ).strip()

        password = request.POST.get(
            'txt_password',
            ''
        )

        # -------------------------------------------------
        # DOCTOR DETAILS
        # -------------------------------------------------

        specialization = request.POST.get(
            'txt_specialization',
            'General Medicine'
        ).strip()

        qualification = request.POST.get(
            'txt_qualification',
            ''
        ).strip()

        license_no = request.POST.get(
            'txt_license_no',
            ''
        ).strip()

        hospital = request.POST.get(
            'txt_hospital',
            ''
        ).strip()

        # -------------------------------------------------
        # EXPERIENCE
        # -------------------------------------------------

        try:

            experience = int(
                request.POST.get(
                    'txt_experience',
                    0
                ) or 0
            )

        except (ValueError, TypeError):

            experience = 0

        experience = max(
            0,
            experience
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name:

            return render(
                request,
                'Doctor/DoctorRegistration.html',
                {
                    'error': 'Name is required.'
                }
            )

        if not email:

            return render(
                request,
                'Doctor/DoctorRegistration.html',
                {
                    'error': 'Email is required.'
                }
            )

        if not contact:

            return render(
                request,
                'Doctor/DoctorRegistration.html',
                {
                    'error': 'Contact is required.'
                }
            )

        if not password:

            return render(
                request,
                'Doctor/DoctorRegistration.html',
                {
                    'error': 'Password is required.'
                }
            )

        # -------------------------------------------------
        # CHECK EMAIL
        # -------------------------------------------------

        if tbl_registration.objects.filter(
            user_email=email
        ).exists():

            return render(
                request,
                'Doctor/DoctorRegistration.html',
                {
                    'error': 'Email already registered.'
                }
            )

        # -------------------------------------------------
        # CREATE REGISTRATION
        # -------------------------------------------------

        registration = tbl_registration.objects.create(

            user_name=name,

            user_email=email,

            user_contact=contact,

            user_address=address,

            user_password=make_password(
                password
            ),

            role='DOCTOR',

            is_active=True
        )

        # -------------------------------------------------
        # CREATE DOCTOR PROFILE
        # -------------------------------------------------

        tbl_Doctor.objects.create(

            user=registration,

            name=name,

            specialization=specialization,

            qualification=qualification,

            license_no=license_no,

            experience=experience,

            hospital=hospital,

            contact=contact,

            available=True
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        messages.success(
            request,
            'Doctor registration successful! Please login.'
        )

        return redirect(
            'Guest:DoctorLogin'
        )

    # -----------------------------------------------------
    # GET REGISTRATION PAGE
    # -----------------------------------------------------

    return render(
        request,
        'Doctor/DoctorRegistration.html'
    )