from datetime import date, timedelta
from django.db.models import Q
from .ml_model import predict_maternal_risk
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.shortcuts import render, redirect

from .models import (
    tbl_PregnancyTracker
)

from .ml_model import nutrition_recommendations
from Guest.models import tbl_registration

from Doctor.models import (
    tbl_Doctor,
    tbl_Appointment,
    tbl_Prescription,
    tbl_Message
)

from Administrator.models import (
    tbl_Milestone,
    tbl_Nutrition
)

from django.http import JsonResponse

from .models import (
    tbl_UserProfile,
    tbl_PregnancyTracker,
    tbl_PregnancyWeeklyRecord,
    tbl_Baby,
    tbl_AIChatMessage
)

from .gemini_service import (
    call_gemini_api,
    get_gemini_api_key,
    get_offline_pregnancy_response
)

from .ml_model import (
    predict_maternal_risk,
    nutrition_recommendations,
    is_data_in_dataset
)

def current_user(request):
    uid = request.session.get('user_id')
    if not uid or request.session.get('role') != 'USER':
        return None
    return tbl_registration.objects.filter(id=uid, is_active=True).first()

def guard(request):
    user = current_user(request)
    if not user:
        return None, redirect('Guest:Login')
    return user, None

def pregnancy_week_for(lmp_date):
    return max(1, min(41, (date.today() - lmp_date).days // 7 + 1))

def pregnancy_is_complete(lmp_date):
    return (date.today() - lmp_date).days >= 41 * 7

def save_completed_pregnancy_weeks(pregnancy, current_week, pregnancy_complete):
    last_completed_week = current_week if pregnancy_complete else current_week - 1
    for week in range(1, last_completed_week + 1):
        pregnancy.weekly_records.get_or_create(week=week)

def UserDashboard(request):
    user, response = guard(request)
    if response: return response
    pregnancy = user.pregnancy_records.first()
    baby = user.babies.first()
    risk = None
    if pregnancy:
        user_prof = user.user_profile.first()
        prof_age = (user_prof.age if user_prof and user_prof.age else 28)
        risk = predict_maternal_risk(
            age=prof_age,
            systolicbp=120, diastolicbp=80, blood_sugar=7,
            bodytemp=98.6, heartrate=78
        )
    return render(request,'User/UserDashboard.html',{
        'user':user,'pregnancy':pregnancy,'baby':baby,'risk':risk,
        'appointments':user.appointments.select_related('doctor').all()[:5]
    })

def PregnancyProfile(request):
    user, response = guard(request)
    if response: return response
    pregnancy = user.pregnancy_records.first()
    if request.method == 'POST':
        if pregnancy and not pregnancy_is_complete(pregnancy.last_period_date):
            messages.error(request, 'Your Last Period Date is saved and cannot be changed during this pregnancy.')
            return redirect('User:PregnancyProfile')
        if pregnancy:
            save_completed_pregnancy_weeks(
                pregnancy,
                pregnancy_week_for(pregnancy.last_period_date),
                pregnancy_is_complete(pregnancy.last_period_date),
            )
        lmp = request.POST.get('last_period_date', '')
        try:
            lmp_date = date.fromisoformat(lmp)
        except ValueError:
            messages.error(request, 'Please enter a valid Last Period Date.')
        else:
            if lmp_date > date.today():
                messages.error(request, 'Last Period Date cannot be in the future.')
            else:
                current_week = pregnancy_week_for(lmp_date)
                tbl_PregnancyTracker.objects.create(
                    user=user,
                    last_period_date=lmp_date,
                    expected_delivery_date=lmp_date + timedelta(days=280),
                    current_week=current_week,
                )
                messages.success(request, 'Pregnancy profile saved. Previous pregnancy records were preserved.')
                return redirect('User:PregnancyTracker')

    current_week = pregnancy_week_for(pregnancy.last_period_date) if pregnancy else None
    pregnancy_complete = pregnancy_is_complete(pregnancy.last_period_date) if pregnancy else False
    if pregnancy and pregnancy.current_week != current_week:
        pregnancy.current_week = current_week
        pregnancy.save(update_fields=['current_week', 'updated_at'])
    return render(request, 'User/PregnancyProfile.html', {
        'user': user,
        'pregnancy': pregnancy,
        'current_week': current_week,
        'current_month': pregnancy.current_month if pregnancy else None,
        'pregnancy_complete': pregnancy_complete,
    })

def PregnancyTracker(request):
    user, response = guard(request)
    if response: return response
    pregnancy = user.pregnancy_records.first()
    has_pregnancy = bool(pregnancy and pregnancy.last_period_date)
    if has_pregnancy:
        current_week = pregnancy_week_for(pregnancy.last_period_date)
        if pregnancy.current_week != current_week:
            pregnancy.current_week = current_week
            pregnancy.save(update_fields=['current_week', 'updated_at'])
        pregnancy_complete = pregnancy_is_complete(pregnancy.last_period_date)
        save_completed_pregnancy_weeks(pregnancy, current_week, pregnancy_complete)
        current_month = pregnancy.current_month
        selected_week = current_week
        available_weeks = range(current_week, 42)
        milestone = tbl_Milestone.objects.filter(week=selected_week).first()
        milestones = tbl_Milestone.objects.filter(week=selected_week)
        weekly_nutrition = []
        nutrition_focus = ""
        if current_week <= 40:
            weekly_nutrition = nutrition_recommendations(pregnancy_week=current_week, limit=8)
            try:
                from .nutrition_data import WEEKLY_NUTRITION
                nutrition_focus = WEEKLY_NUTRITION.get(current_week, {}).get("focus", "")
            except Exception:
                nutrition_focus = ""
    else:
        current_week = None
        current_month = None
        selected_week = None
        available_weeks = []
        milestone = None
        milestones = tbl_Milestone.objects.none()
        weekly_nutrition = []
        nutrition_focus = ""
        pregnancy_complete = False

    return render(request, 'User/PregnancyTracker.html', {
        'user': user,
        'pregnancy': pregnancy,
        'has_pregnancy': has_pregnancy,
        'current_week': current_week,
        'current_month': current_month,
        'selected_week': selected_week,
        'available_weeks': available_weeks,
        'milestone': milestone,
        'milestones': milestones,
        'weekly_nutrition': weekly_nutrition,
        'nutrition_focus': nutrition_focus,
        'pregnancy_complete': pregnancy_complete,
    })

def WeeklyRecordHistory(request):
    user, response = guard(request)
    if response: return response
    pregnancy = user.pregnancy_records.first()
    if pregnancy:
        current_week = pregnancy_week_for(pregnancy.last_period_date)
        pregnancy_complete = pregnancy_is_complete(pregnancy.last_period_date)
        save_completed_pregnancy_weeks(pregnancy, current_week, pregnancy_complete)
    weekly_records = tbl_PregnancyWeeklyRecord.objects.filter(
        pregnancy__user=user
    ).select_related('pregnancy').order_by('-pregnancy__created_at', '-week', '-recorded_at')
    selected_week = None
    if pregnancy:
        try:
            requested_week = int(request.GET.get('week', ''))
            if 1 <= requested_week <= 41:
                selected_week = requested_week
        except (TypeError, ValueError):
            nutrition_focus = ""
            pass

    if selected_week and selected_week <= 40:
        weekly_nutrition = nutrition_recommendations(pregnancy_week=selected_week, limit=8)
        try:
            from .nutrition_data import WEEKLY_NUTRITION
            nutrition_focus = WEEKLY_NUTRITION.get(selected_week, {}).get("focus", "")
        except Exception:
            nutrition_focus = ""
    else:
        weekly_nutrition = []
        nutrition_focus = ""

    return render(request, 'User/WeeklyRecordHistory.html', {
        'user': user,
        'weekly_records': weekly_records,
        'selected_week': selected_week,
        'weekly_nutrition': weekly_nutrition,
        'nutrition_focus': nutrition_focus,
    })

def BabyGrowth(request):
    user,response=guard(request)
    if response:return response
    baby=user.babies.first()
    if request.method=='POST':
        baby=tbl_Baby.objects.create(
            user=user,baby_name=request.POST.get('baby_name',''),
            date_of_birth=request.POST.get('date_of_birth') or None,
            gender=request.POST.get('gender',''),birth_weight=request.POST.get('birth_weight') or None,
            current_weight=request.POST.get('current_weight') or None,
            height=request.POST.get('height') or None,notes=request.POST.get('notes','')
        )
        messages.success(request,'Baby record saved.')
        return redirect('User:BabyGrowth')
    return render(request,'User/BabyGrowth.html',{'user':user,'baby':baby,'babies':user.babies.all()})

def Nutrition(request):
    user = current_user(request)
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    pregnancy = user.pregnancy_records.first() if user else None
    current_week = pregnancy.current_week if pregnancy else None

    # Week-based nutrition recommendations with search and category filtering
    nutrition_list = nutrition_recommendations(
        pregnancy_week=current_week,
        query=search,
        category=category,
        limit=24
    )

    return render(
        request,
        "User/Nutrition.html",
        {
            "nutrition": nutrition_list,
            "current_week": current_week,
            "search": search,
            "category": category,
            "user": user,
        }
    )


def Appointments(request):

    user, response = guard(request)
    if response:
        return response

    doctors = tbl_Doctor.objects.filter(
        available=True
    ).select_related('user')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor') or request.POST.get('doctor_id')
        doctor = get_object_or_404(
            tbl_Doctor,
            id=doctor_id,
            available=True
        )

        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason', '').strip()

        if not appointment_date or not appointment_time:
            messages.error(request, 'Please select both an appointment date and time.')
            return redirect('User:Appointments')

        tbl_Appointment.objects.create(
            patient=user,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Pending'
        )

        messages.success(
            request,
            f'Appointment with Dr. {doctor.name} booked successfully! Once confirmed by the doctor, you can start messaging.'
        )

        return redirect('User:Appointments')

    appointments = tbl_Appointment.objects.filter(
        patient=user
    ).select_related(
        'doctor',
        'doctor__user'
    ).order_by('-appointment_date', '-appointment_time')

    return render(
        request,
        'User/Appointments.html',
        {
            'user': user,
            'doctors': doctors,
            'Doctors': doctors,
            'appointments': appointments,
            'Appointments': appointments
        }
    )

def Profile(request):
    user, response = guard(request)
    if response:
        return response

    profile, _ = tbl_UserProfile.objects.get_or_create(
        user=user,
        defaults={'contact': user.user_contact, 'address': user.user_address}
    )

    if request.method == 'POST':
        user_name = request.POST.get('user_name', '').strip()
        user_email = request.POST.get('user_email', '').strip().lower()
        user_contact = request.POST.get('user_contact', '').strip()
        user_address = request.POST.get('user_address', '').strip()
        dob_str = request.POST.get('date_of_birth', '').strip()
        age_str = request.POST.get('age', '').strip()

        if not user_name:
            messages.error(request, 'Please enter your full name.')
            return render(
                request,
                'User/Profile.html',
                {'user': user, 'registration': user, 'profile': profile}
            )

        if user_email:
            if tbl_registration.objects.filter(user_email=user_email).exclude(id=user.id).exists():
                messages.error(request, 'This email address is already in use by another account.')
                return render(
                    request,
                    'User/Profile.html',
                    {'user': user, 'registration': user, 'profile': profile}
                )
            user.user_email = user_email

        user.user_name = user_name
        user.user_contact = user_contact
        user.user_address = user_address
        user.save()

        # Update session user name for header/greeting
        request.session['user_name'] = user.user_name

        profile.contact = user_contact
        profile.address = user_address

        if dob_str:
            try:
                from datetime import datetime
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                profile.date_of_birth = dob
                today = date.today()
                calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                profile.age = max(0, calculated_age)
            except Exception:
                if age_str and age_str.isdigit():
                    profile.age = int(age_str)
        elif age_str and age_str.isdigit():
            profile.age = int(age_str)

        if 'profile_photo' in request.FILES and request.FILES['profile_photo']:
            profile.profile_photo = request.FILES['profile_photo']

        profile.save()

        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('User:MyProfile')

    return render(
        request,
        'User/Profile.html',
        {
            'user': user,
            'registration': user,
            'profile': profile
        }
    )

def MyProfile(request):
    user, response = guard(request)
    if response:
        return response

    profile, _ = tbl_UserProfile.objects.get_or_create(
        user=user,
        defaults={'contact': user.user_contact, 'address': user.user_address}
    )

    pregnancy = tbl_PregnancyTracker.objects.filter(user=user).order_by('-updated_at').first()

    return render(
        request,
        'User/MyProfile.html',
        {
            'user': user,
            'registration': user,
            'profile': profile,
            'pregnancy': pregnancy
        }
    )

def Messages(request):
    user, response = guard(request)
    if response:
        return response

    # 1. Fetch only doctors with whom this patient has an 'Approved' (confirmed) appointment
    confirmed_appointments = tbl_Appointment.objects.filter(
        patient=user,
        status='Approved'
    ).select_related('doctor', 'doctor__user').order_by('-appointment_date')

    confirmed_doctor_ids = confirmed_appointments.values_list('doctor_id', flat=True).distinct()
    confirmed_doctors = tbl_Doctor.objects.filter(id__in=confirmed_doctor_ids).select_related('user')

    # Pending appointments (to inform the user if waiting)
    pending_appointments = tbl_Appointment.objects.filter(
        patient=user,
        status='Pending'
    ).select_related('doctor')

    # Selected doctor (e.g. from ?doctor=<id> or POST)
    selected_doctor_id = request.GET.get('doctor') or request.POST.get('doctor') or request.POST.get('doctor_id')
    try:
        selected_doctor_id = int(selected_doctor_id) if selected_doctor_id else None
    except (ValueError, TypeError):
        selected_doctor_id = None

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor') or request.POST.get('doctor_id')
        message_text = request.POST.get('message', '').strip()

        if not doctor_id:
            messages.error(request, 'Please select a confirmed doctor to message.')
            return redirect('User:Messages')

        doctor = get_object_or_404(tbl_Doctor, id=doctor_id)

        # STRICT ENFORCEMENT: Patient must have an Approved appointment with this doctor
        has_approved = tbl_Appointment.objects.filter(
            patient=user,
            doctor=doctor,
            status='Approved'
        ).exists()

        if not has_approved:
            messages.error(
                request,
                f'You cannot chat with Dr. {doctor.name}. Your appointment must be booked and confirmed by the doctor before messaging.'
            )
            return redirect('User:Messages')

        if not message_text:
            messages.error(request, 'Message cannot be empty.')
            return redirect(f"/User/Messages/?doctor={doctor.id}")

        tbl_Message.objects.create(
            sender=user,
            receiver=doctor.user,
            message=message_text
        )
        messages.success(request, f'Message sent to Dr. {doctor.name}.')
        return redirect(f"/User/Messages/?doctor={doctor.id}")

    # Messages between user and doctors
    doctor_user_ids = confirmed_doctors.values_list('user_id', flat=True)
    msgs = tbl_Message.objects.filter(
        (Q(sender=user) & Q(receiver_id__in=doctor_user_ids)) |
        (Q(receiver=user) & Q(sender_id__in=doctor_user_ids))
    ).select_related('sender', 'receiver').order_by('sent_at')

    # Default to first confirmed doctor if not selected
    if not selected_doctor_id and confirmed_doctors.exists():
        selected_doctor_id = confirmed_doctors.first().id

    # Active conversation filter
    active_doctor = None
    if selected_doctor_id:
        active_doctor = confirmed_doctors.filter(id=selected_doctor_id).first()
        if active_doctor:
            conversation = msgs.filter(
                Q(sender=active_doctor.user) | Q(receiver=active_doctor.user)
            )
        else:
            conversation = msgs
    else:
        conversation = msgs

    return render(
        request,
        'User/Messages.html',
        {
            'user': user,
            'confirmed_doctors': confirmed_doctors,
            'doctors': confirmed_doctors,
            'pending_appointments': pending_appointments,
            'messages_list': msgs,
            'conversation': conversation,
            'active_doctor': active_doctor,
            'selected_doctor_id': selected_doctor_id,
            'has_confirmed_doctor': confirmed_doctors.exists(),
        }
    )

PREGNANCY_SYMPTOM_OPTIONS = [
    ('heavy_bleeding', 'Heavy vaginal bleeding'),
    ('severe_abdominal_pain', 'Severe abdominal pain'),
    ('fainting', 'Fainting or severe dizziness'),
    ('breathing_chest_pain', 'Difficulty breathing or chest pain'),
    ('severe_headache_vision', 'Severe headache or vision changes'),
    ('fever', 'Fever of 38 C (100.4 F) or higher'),
    ('reduced_fetal_movement', 'Reduced or absent fetal movement'),
    ('nausea', 'Nausea'),
    ('mild_cramps', 'Mild cramps'),
    ('fatigue', 'Fatigue'),
    ('back_pain', 'Back pain'),
    ('none', 'No symptoms'),
]

URGENT_PREGNANCY_SYMPTOMS = {
    'heavy_bleeding',
    'severe_abdominal_pain',
    'fainting',
    'breathing_chest_pain',
    'severe_headache_vision',
    'fever',
    'reduced_fetal_movement',
}


def assess_pregnancy_screening(age, period_delay_days, symptoms):
    urgent_symptoms = [
        label for value, label in PREGNANCY_SYMPTOM_OPTIONS
        if value in symptoms and value in URGENT_PREGNANCY_SYMPTOMS
    ]
    selected_labels = [
        label for value, label in PREGNANCY_SYMPTOM_OPTIONS
        if value in symptoms and value != 'none'
    ]
    findings = []

    if age < 18 or age >= 35:
        findings.append('Age can affect pregnancy care needs; discuss your situation with a healthcare professional.')
    else:
        findings.append('Age alone cannot determine pregnancy risk.')

    if period_delay_days >= 7:
        findings.append('If pregnancy is possible, take a home pregnancy test and contact a healthcare professional if it is positive or your period remains delayed.')
    elif period_delay_days > 0:
        findings.append('A short period delay does not confirm pregnancy. Consider testing if your period remains delayed.')
    else:
        findings.append('No period delay was reported.')

    if urgent_symptoms:
        label = 'Urgent medical attention recommended'
        guidance = 'These symptoms can require urgent assessment during pregnancy. Contact your maternity care team or local emergency service now.'
        level = 'urgent'
    elif period_delay_days >= 7:
        label = 'Pregnancy test recommended'
        guidance = 'A delayed period cannot confirm pregnancy. Use a pregnancy test and seek professional advice as needed.'
        level = 'warning'
    elif age < 18 or age >= 35:
        label = 'Discuss with a healthcare professional'
        guidance = 'Age is only one factor and cannot predict an individual pregnancy outcome.'
        level = 'warning'
    else:
        label = 'No urgent warning symptoms selected'
        guidance = 'This screening does not rule out a health problem. Contact a healthcare professional about symptoms or concerns.'
        level = 'info'

    if selected_labels:
        findings.append('Selected symptoms: ' + ', '.join(selected_labels) + '.')
    else:
        findings.append('No symptoms were selected.')

    return {
        'label': label,
        'guidance': guidance,
        'findings': findings,
        'level': level,
    }


def pregnancy_possibility_status(period_delay_days):
    if period_delay_days == 0:
        return (
            'These details cannot determine pregnancy. Symptoms alone cannot confirm or rule it out. '
            'If pregnancy is possible, take a test if your period becomes late.'
        )
    if period_delay_days >= 7:
        return (
            'Pregnancy is possible, but age, symptoms, and a delayed period cannot confirm it. '
            'Take a home pregnancy test.'
        )
    return (
        'Pregnancy is possible, but a short delay can have other causes and symptoms cannot confirm it. '
        'Test if your period remains delayed.'
    )


def ai_pregnancy_screening(
    age,
    period_delay_days,
    symptoms,
    request=None,
):
    if age < 18:
        if age < 10:
            guidance = (
                'This screening cannot assess children under 10. Pregnancy at age 4 is exceptionally rare, '
                'but any concern needs immediate assessment by a pediatric medical professional. If the '
                'child has severe symptoms or may be in immediate danger, contact emergency services and '
                'local child-protection services now. This child\'s information will not be sent to AI.'
            )
            label = 'Immediate pediatric assessment needed'
        else:
            guidance = (
                'This screening is intended for adults. For anyone under 18 who may be pregnant, involve '
                'a trusted adult and contact a pediatric or maternity-care professional promptly. For '
                'severe symptoms or immediate danger, contact emergency and child-protection services. '
                'This minor\'s information will not be sent to AI.'
            )
            label = 'Adult screening unavailable for minors'
        return {
            'label': label,
            'guidance': guidance,
            'findings': [],
            'level': 'urgent' if age < 10 or any(
                symptom in URGENT_PREGNANCY_SYMPTOMS for symptom in symptoms
            ) else 'warning',
            'pregnancy_status': 'Not assessed',
            'source': 'Child-safety rules; AI not used',
        }

    symptom_labels = [
        label for value, label in PREGNANCY_SYMPTOM_OPTIONS
        if value in symptoms and value != 'none'
    ]
    prompt = (
        "Provide cautious, concise pregnancy-health screening guidance using only these inputs. "
        "Do not diagnose pregnancy or a medical condition, give a risk percentage, or claim certainty. "
        "The application has already calculated a cautious pregnancy-possibility status. Do not contradict "
        "it or claim the person is pregnant/not pregnant. Give only brief next-step guidance. Explain that "
        "symptoms and period delay cannot confirm pregnancy. For severe symptoms, advise urgent contact "
        "with maternity care or emergency services. Mention that this is educational and not a substitute "
        "for a clinician. Inputs: "
        f"age={age} years; period delay={period_delay_days} days; "
        f"application pregnancy-possibility status={pregnancy_possibility_status(period_delay_days)}; "
        f"selected symptoms={', '.join(symptom_labels) if symptom_labels else 'none'}"
    )
    pregnancy_status = pregnancy_possibility_status(period_delay_days)
    api_key = get_gemini_api_key(request)
    if api_key:
        ai_result, _ = call_gemini_api(
            [{'role': 'user', 'text': prompt}],
            api_key=api_key,
        )
        if ai_result and ai_result.get('reply'):
            urgent_selected = any(
                symptom in URGENT_PREGNANCY_SYMPTOMS for symptom in symptoms
            )
            if urgent_selected:
                result = assess_pregnancy_screening(age, period_delay_days, symptoms)
                result['source'] = 'Gemini AI with urgent-symptom safety guidance'
                result['pregnancy_status'] = pregnancy_status
                return result
            return {
                'label': 'AI screening guidance',
                'guidance': ai_result['reply'],
                'show_ai_guidance': True,
                'findings': [],
                'level': 'info',
                'pregnancy_status': pregnancy_status,
                'source': f"Gemini AI ({ai_result.get('model', 'configured model')})",
            }

    result = assess_pregnancy_screening(age, period_delay_days, symptoms)
    result['pregnancy_status'] = pregnancy_status
    result['source'] = 'Rule-based fallback; AI service unavailable'
    return result


def AIPrediction(request):
    user, response = guard(request)
    if response: return response
    result = None
    error = None
    form_data = {}
    form_errors = {}

    if request.method == "POST":
        raw_age = (request.POST.get("age") or "").strip()
        raw_period_delay = (request.POST.get("period_delay_days") or "").strip()
        symptoms = request.POST.getlist("symptoms")
        valid_symptoms = {value for value, _ in PREGNANCY_SYMPTOM_OPTIONS}

        form_data = {
            "age": raw_age,
            "period_delay_days": raw_period_delay,
            "symptoms": symptoms,
        }

        if not raw_age:
            form_errors['age'] = 'Enter your age in completed years.'
        else:
            try:
                age = int(raw_age)
                if not 1 <= age <= 120:
                    form_errors['age'] = 'Age must be between 1 and 120 years.'
            except (ValueError, TypeError):
                form_errors['age'] = 'Age must be a whole number.'

        if not raw_period_delay:
            form_errors['period_delay_days'] = 'Enter a delay in whole days; enter 0 if your period is not late.'
        else:
            try:
                period_delay_days = int(raw_period_delay)
                if not 0 <= period_delay_days <= 365:
                    form_errors['period_delay_days'] = 'Period delay must be between 0 and 365 days.'
            except (ValueError, TypeError):
                form_errors['period_delay_days'] = 'Period delay must be a whole number of days.'

        if not symptoms:
            form_errors['symptoms'] = 'Select at least one symptom or choose No symptoms.'
        elif any(symptom not in valid_symptoms for symptom in symptoms):
            form_errors['symptoms'] = 'Choose symptoms from the list or clear the selection.'
        elif 'none' in symptoms and len(symptoms) > 1:
            form_errors['symptoms'] = 'Choose No symptoms by itself, or select the symptoms that apply.'

        if form_errors:
            error = 'Please correct the highlighted fields.'
        else:
            result = ai_pregnancy_screening(
                age,
                period_delay_days,
                symptoms,
                request=request,
            )

    return render(request, "User/AIPrediction.html", {
        "user": user,
        "result": result,
        "error": error,
        "form_data": form_data,
        "form_errors": form_errors,
        "symptom_options": PREGNANCY_SYMPTOM_OPTIONS,
    })


def AIPredictionValues(request):
    user, response = guard(request)
    if response: return response

    field_specs = {
        'age': ('Age', int, 10, 70),
        'systolic': ('Systolic blood pressure', int, 60, 220),
        'diastolic': ('Diastolic blood pressure', int, 30, 150),
        'blood_sugar': ('Blood sugar', float, 1, 30),
        'body_temperature': ('Body temperature', float, 90, 110),
        'heart_rate': ('Heart rate', int, 30, 220),
    }
    form_data = {key: '' for key in field_specs}
    form_errors = {}
    result = None

    if request.method == 'POST':
        values = {}
        for key, (label, converter, minimum, maximum) in field_specs.items():
            raw_value = (request.POST.get(key) or '').strip()
            form_data[key] = raw_value
            if not raw_value:
                form_errors[key] = f'Enter {label.lower()}.'
                continue
            try:
                value = converter(raw_value)
            except (ValueError, TypeError):
                form_errors[key] = f'Enter a valid {label.lower()} value.'
                continue
            if not minimum <= value <= maximum:
                form_errors[key] = f'{label} must be between {minimum} and {maximum}.'
                continue
            values[key] = value

        if not form_errors:
            result = predict_maternal_risk(
                age=values['age'],
                systolicbp=values['systolic'],
                diastolicbp=values['diastolic'],
                blood_sugar=values['blood_sugar'],
                bodytemp=values['body_temperature'],
                heartrate=values['heart_rate'],
            )

    return render(request, 'User/AIPredictionValues.html', {
        'user': user,
        'form_data': form_data,
        'form_errors': form_errors,
        'result': result,
    })


# def AIPrediction(request):

#     result = None
#     recommended_foods = []

#     if request.method == "POST":

#         try:

#             age = float(
#                 request.POST.get("age")
#             )

#             systolic = float(
#                 request.POST.get("systolic")
#             )

#             diastolic = float(
#                 request.POST.get("diastolic")
#             )

#             blood_sugar = float(
#                 request.POST.get("blood_sugar")
#             )

#             body_temperature = float(
#                 request.POST.get("body_temperature")
#             )

#             heart_rate = float(
#                 request.POST.get("heart_rate")
#             )


#             # -----------------------------------------
#             # ML PREDICTION
#             # -----------------------------------------

#             risk_level = predict_maternal_risk(
#                 age,
#                 systolic,
#                 diastolic,
#                 blood_sugar,
#                 body_temperature,
#                 heart_rate
#             )


#             # -----------------------------------------
#             # NUTRITION RECOMMENDATION
#             # -----------------------------------------

#             recommended_foods = nutrition_recommendations(
#                 risk_level
#             )


#             # -----------------------------------------
#             # RESULT MESSAGE
#             # -----------------------------------------

#             result = {

#                 "risk": risk_level,

#                 "message":
#                     "Nutrition recommendations are generated based on the predicted health risk."

#             }


#         except Exception as e:

#             result = {

#                 "risk": "Prediction Error",

#                 "message": str(e)

#             }


#     return render(
#         request,
#         "User/AIPrediction.html",
#         {
#             "result": result,
#             "recommended_foods": recommended_foods
#         }
#     )

# def predict_health_risk(request):
#     context = {}

#     if request.method == 'POST':
#         # Retrieve form data
#         age = float(request.POST.get('age', 0))
#         systolic = float(request.POST.get('systolic', 0))
#         diastolic = float(request.POST.get('diastolic', 0))
#         blood_sugar = float(request.POST.get('blood_sugar', 0))
#         body_temperature = float(request.POST.get('body_temperature', 0))
#         heart_rate = float(request.POST.get('heart_rate', 0))

#         # Example ML model prediction logic (replace with your trained ML model loading & prediction)
#         # e.g., risk = ml_model.predict([[age, systolic, diastolic, blood_sugar, body_temperature, heart_rate]])
        
#         if blood_sugar > 7.0 or systolic > 140 or diastolic > 90:
#             risk = "High Risk"
#             message = "High blood pressure or blood sugar detected. A low-sodium and high-fiber diet is advised."
#         elif blood_sugar > 5.5 or systolic > 125:
#             risk = "Mid Risk"
#             message = "Slight elevation in metrics. Maintain a balanced nutrient-dense diet."
#         else:
#             risk = "Low Risk"
#             message = "Vital signs are in the healthy range. Continue with standard daily nutrition."

#         context['result'] = {
#             'risk': risk,
#             'message': message,
#         }

#         # Query or retrieve food recommendations based on risk level
#         # (This can be pulled from a Django Model or filtered pandas dataframe)
#         recommended_foods = [
#             {
#                 'name': 'Spinach',
#                 'category': 'Vegetables A-E',
#                 'calories': '23 kcal',
#                 'protein': '2.9 g',
#                 'iron': '2.7 mg',
#                 'calcium': '99 mg',
#                 'fiber': '2.2 g',
#                 'recommendation': 'Rich in essential minerals and fiber, ideal for regulating blood pressure.',
#             },
#             {
#                 'name': 'Oatmeal',
#                 'category': 'Breads, cereals, fastfood, grains',
#                 'calories': '150 kcal',
#                 'protein': '5.0 g',
#                 'iron': '1.5 mg',
#                 'calcium': '20 mg',
#                 'fiber': '4.0 g',
#                 'recommendation': 'High soluble fiber content supports stable blood glucose levels.',
#             },
#         ]

#         context['recommended_foods'] = recommended_foods

#     return render(request, 'User/AIPrediction.html', context)


def AIChatbot(request):
    user, response = guard(request)
    if response:
        return response

    pregnancy = user.pregnancy_records.first()
    baby = user.babies.first()
    pregnancy_week = pregnancy.current_week if (pregnancy and pregnancy.last_period_date) else None
    due_date = pregnancy.expected_delivery_date.strftime('%B %d, %Y') if (pregnancy and pregnancy.expected_delivery_date) else None
    baby_name = baby.baby_name if baby else None

    user_context = {
        "user_name": user.user_name,
        "pregnancy_week": pregnancy_week,
        "due_date": due_date,
        "baby_name": baby_name,
    }

    if request.method == "POST":
        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or "application/json" in request.content_type
        )
        if is_ajax and request.body:
            import json
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception:
                data = {}
        else:
            data = request.POST

        action = data.get("action", "send_message")

        # Handle API key update
        if action == "save_api_key":
            api_key = data.get("api_key", "").strip()
            request.session["gemini_api_key"] = api_key
            if is_ajax:
                return JsonResponse({"status": "success", "message": "Gemini API Key saved."})
            messages.success(request, "Gemini API Key saved successfully.")
            return redirect("User:AIChatbot")

        # Handle clear chat
        if action == "clear_chat":
            tbl_AIChatMessage.objects.filter(user=user).delete()
            if is_ajax:
                return JsonResponse({"status": "success", "message": "Chat history cleared."})
            messages.success(request, "Chat history cleared.")
            return redirect("User:AIChatbot")

        # Send user message
        user_message = data.get("message", "").strip()
        if not user_message:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Please enter a message."}, status=400)
            return redirect("User:AIChatbot")

        # Save user message to database
        tbl_AIChatMessage.objects.create(
            user=user,
            sender="USER",
            message=user_message
        )

        # Retrieve recent history for Gemini conversation context
        recent_chats = tbl_AIChatMessage.objects.filter(user=user).order_by("created_at")
        history = []
        for c in recent_chats:
            history.append({
                "role": "user" if c.sender == "USER" else "model",
                "text": c.message
            })

        api_key = get_gemini_api_key(request)
        gemini_result, gemini_error = call_gemini_api(history, user_context=user_context, api_key=api_key)

        if gemini_result and gemini_result.get("reply"):
            bot_reply = gemini_result["reply"]
            source = gemini_result.get("source", "gemini")
            model_used = gemini_result.get("model", "gemini-1.5-flash")
        else:
            bot_reply = get_offline_pregnancy_response(user_message, user_context=user_context)
            source = "offline_knowledge"
            model_used = "Offline Medical Advisor"

        # Save bot reply to database
        bot_chat = tbl_AIChatMessage.objects.create(
            user=user,
            sender="BOT",
            message=bot_reply
        )

        if is_ajax:
            return JsonResponse({
                "status": "success",
                "reply": bot_reply,
                "sender": "BOT",
                "source": source,
                "model": model_used,
                "created_at": bot_chat.created_at.strftime("%I:%M %p")
            })

        return redirect("User:AIChatbot")

    # GET Request
    chat_history = tbl_AIChatMessage.objects.filter(user=user).order_by("created_at")
    current_key = get_gemini_api_key(request)
    has_api_key = bool(current_key)
    masked_key = (current_key[:6] + "..." + current_key[-4:]) if (has_api_key and len(current_key) > 10) else ("Active" if has_api_key else "")

    return render(request, "User/AIChatbot.html", {
        "user": user,
        "pregnancy": pregnancy,
        "pregnancy_week": pregnancy_week,
        "chat_history": chat_history,
        "has_api_key": has_api_key,
        "masked_key": masked_key,
        "user_context": user_context,
    })