from pathlib import Path
import joblib
import pandas as pd
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render
from Guest.models import tbl_registration
from Doctor.models import tbl_Doctor, tbl_Appointment
from User.models import tbl_PregnancyTracker
from User.ml_model import MODEL_PATH, ENCODER_PATH
from .models import tbl_Milestone, tbl_Nutrition, tbl_Medicine, tbl_Dataset


def admin_guard(request):
    if request.session.get('role') != 'ADMIN':
        return redirect('Guest:Login')
    return None


def AdminDashboard(request):
    if (r := admin_guard(request)): return r
    return render(request, 'Administrator/AdminDashboard.html', {
        'users': tbl_registration.objects.filter(role='USER').count(),
        'doctors': tbl_Doctor.objects.count(),
        'appointments': tbl_Appointment.objects.count(),
        'pregnancies': tbl_PregnancyTracker.objects.count(),
        'datasets': tbl_Dataset.objects.count(),
    })

def ManageUser(request):
    if (r := admin_guard(request)): return r
    if request.method == 'POST':
        uid = request.POST.get('user_id')
        if uid:
            u = get_object_or_404(tbl_registration, id=uid, role='USER')
            u.is_active = not u.is_active
            u.save(update_fields=['is_active'])
        else:
            name = request.POST.get('txt_name', '').strip()
            email = request.POST.get('txt_email', '').strip().lower()
            phone = request.POST.get('txt_phone', request.POST.get('txt_contact', '')).strip()
            if name and email and phone and not tbl_registration.objects.filter(user_email=email).exists():
                tbl_registration.objects.create(user_name=name, user_email=email, user_contact=phone,
                    user_password=make_password('User@123'), role='USER', is_active=True)
            else:
                messages.error(request, 'Enter valid details and use a unique email.')
        return redirect('Administrator:ManageUser')
    return render(request, 'Administrator/ManageUser.html', {'users': tbl_registration.objects.filter(role='USER')})


def ManageDoctor(request):
    if (r := admin_guard(request)): return r
    if request.method == 'POST':
        action = request.POST.get('action', 'add')
        if action == 'toggle':
            d = get_object_or_404(tbl_Doctor, id=request.POST.get('doctor'))
            d.available = not d.available
            d.save(update_fields=['available'])
        elif action == 'delete':
            d = get_object_or_404(tbl_Doctor, id=request.POST.get('doctor'))
            d.user.delete()
        else:
            name = request.POST.get('txt_name', request.POST.get('name', '')).strip()
            email = request.POST.get('txt_email', request.POST.get('email', '')).strip().lower()
            contact = request.POST.get('txt_phone', request.POST.get('contact', '')).strip()
            specialization = request.POST.get('txt_specialization', request.POST.get('specialization', 'General Medicine')).strip()
            qualification = request.POST.get('txt_qualification', '').strip()
            license_no = request.POST.get('txt_license_no', '').strip()
            hospital = request.POST.get('txt_hospital', '').strip()
            password = request.POST.get('txt_password', request.POST.get('password', 'Doctor@123'))
            try: experience = int(request.POST.get('txt_experience', request.POST.get('experience', 0)) or 0)
            except ValueError: experience = 0
            if not name or not email or not contact:
                messages.error(request, 'Name, email and phone are required.')
            elif tbl_registration.objects.filter(user_email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                reg = tbl_registration.objects.create(user_name=name, user_email=email, user_contact=contact,
                    user_address='', user_password=make_password(password), role='DOCTOR', is_active=True)
                tbl_Doctor.objects.create(user=reg, name=name, specialization=specialization or 'General Medicine',
                    qualification=qualification, license_no=license_no, experience=max(0, experience),
                    hospital=hospital, contact=contact, available=True)
                messages.success(request, 'Doctor added successfully.')
        return redirect('Administrator:ManageDoctor')
    return render(request, 'Administrator/ManageDoctor.html', {'doctors': tbl_Doctor.objects.select_related('user').all()})


def EditDoctor(request, pk):
    if (r := admin_guard(request)): return r
    doctor = get_object_or_404(tbl_Doctor, id=pk)
    if request.method == 'POST':
        doctor.name = request.POST.get('name', doctor.name).strip()
        doctor.specialization = request.POST.get('specialization', doctor.specialization)
        doctor.qualification = request.POST.get('qualification', doctor.qualification)
        doctor.license_no = request.POST.get('license_no', doctor.license_no)
        doctor.hospital = request.POST.get('hospital', doctor.hospital)
        doctor.contact = request.POST.get('contact', doctor.contact)
        doctor.user.user_name = doctor.name
        doctor.user.user_contact = doctor.contact
        doctor.user.save()
        doctor.save()
        messages.success(request, 'Doctor updated.')
        return redirect('Administrator:ManageDoctor')
    return render(request, 'Administrator/EditDoctor.html', {'doctor': doctor})


def DeleteDoctor(request, pk):
    if (r := admin_guard(request)): return r
    doctor = get_object_or_404(tbl_Doctor, id=pk)
    doctor.user.delete()
    messages.success(request, 'Doctor deleted.')
    return redirect('Administrator:ManageDoctor')


def ManageMilestones(request):
    if (r := admin_guard(request)): return r
    if request.method == 'POST':
        try: week = int(request.POST.get('week', request.POST.get('txt_week')))
        except (TypeError, ValueError):
            messages.error(request, 'Week must be a number.'); return redirect('Administrator:ManageMilestones')
        tbl_Milestone.objects.update_or_create(week=week, defaults={
            'title': request.POST.get('title', request.POST.get('txt_milestone', '')),
            'description': request.POST.get('description', request.POST.get('txt_description', '')),
            'tips': request.POST.get('tips', '')
        })
        messages.success(request, 'Milestone saved.')
        return redirect('Administrator:ManageMilestones')
    return render(request, 'Administrator/ManageMilestones.html', {'milestones': tbl_Milestone.objects.all()})

def ManageNutrition(request):

    if request.method == "POST":

        name = request.POST.get("name")
        category = request.POST.get("category")
        calories = request.POST.get("calories")
        protein = request.POST.get("protein")
        iron = request.POST.get("iron")
        calcium = request.POST.get("calcium")
        fiber = request.POST.get("fiber")
        recommendation = request.POST.get("recommendation")

        tbl_Nutrition.objects.create(
            name=name,
            category=category,
            calories=calories or None,
            protein=protein or None,
            iron=iron or None,
            calcium=calcium or None,
            fiber=fiber or None,
            recommendation=recommendation
        )

        messages.success(request, "Nutrition added successfully.")

        return redirect("Administrator:ManageNutrition")

    nutrition = tbl_Nutrition.objects.all().order_by("name")

    return render(
        request,
        "Administrator/ManageNutrition.html",
        {
            "nutrition": nutrition
        }
    )


def ManageMedicines(request):

    if request.method == "POST":
        name = request.POST.get("name")
        dosage = request.POST.get("dosage")
        purpose = request.POST.get("purpose")
        warning = request.POST.get("warning")

        tbl_Medicine.objects.create(
            name=name,
            dosage=dosage,
            purpose=purpose,
            warning=warning
        )

        messages.success(request, "Medicine added successfully.")
        return redirect("Administrator:ManageMedicines")

    medicines = tbl_Medicine.objects.all().order_by("id")

    return render(
        request,
        "Administrator/ManageMedicines.html",
        {"medicines": medicines}
    )


def Reports(request):
    if (r := admin_guard(request)): return r
    return render(request, 'Administrator/Reports.html', {
        'users': tbl_registration.objects.filter(role='USER').count(),
        'doctors': tbl_Doctor.objects.count(),
        'appointments': tbl_Appointment.objects.count(),
        'pregnancies': tbl_PregnancyTracker.objects.count()
    })

def UploadDataset(request):
    if (r := admin_guard(request)): return r
    trained = False; error = None
    if request.method == 'POST' and request.FILES.get('dataset'):
        f = request.FILES['dataset']
        dest = Path(__file__).resolve().parent.parent / 'media' / 'datasets'
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / Path(f.name).name
        with open(path, 'wb') as out:
            for chunk in f.chunks(): out.write(chunk)
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder
            df = pd.read_csv(path)
            aliases = {
                'age':['Age','age'], 'systolicbp':['Systolic BP','SystolicBP','systolicbp'],
                'diastolicbp':['Diastolic','DiastolicBP','diastolicbp'],
                'blood_sugar':['BS','Blood sugar','blood_sugar'],
                'bodytemp':['Body Temp','BodyTemp','bodytemp'],
                'heartrate':['Heart Rate','HeartRate','heartrate'],
                'risk':['Risk Level','RiskLevel','risk']
            }
            def find_col(key):
                for c in aliases[key]:
                    if c in df.columns: return c
                return None
            chosen = {k: find_col(k) for k in aliases}
            if not all(chosen.values()): raise ValueError('Dataset must contain Age, blood pressure, blood sugar, body temperature, heart rate and Risk Level columns.')
            d = df[[chosen[k] for k in ['age','systolicbp','diastolicbp','blood_sugar','bodytemp','heartrate','risk']]].dropna()
            X = d.iloc[:, :6].astype(float)
            enc = LabelEncoder(); y = enc.fit_transform(d.iloc[:, 6].astype(str).str.lower())
            model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced').fit(X, y)
            joblib.dump(model, MODEL_PATH); joblib.dump(enc, ENCODER_PATH)
            tbl_Dataset.objects.create(name=f.name, file=f'datasets/{f.name}', rows=len(df))
            trained = True
        except Exception as exc:
            error = str(exc)
    return render(request, 'Administrator/UploadDataset.html', {'trained': trained, 'error': error, 'datasets': tbl_Dataset.objects.all()})


def ChatBox(request):
    if (r := admin_guard(request)): return r
    answer = None
    if request.method == 'POST':
        q = request.POST.get('message', '').strip().lower()
        answer = ('Use the AI Prediction page for numeric maternal risk assessment.' if 'risk' in q
                  else 'The system connects pregnancy tracking, nutrition, appointments, doctors and maternal-risk ML prediction.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'answer': answer})
    return render(request, 'Administrator/ChatBox.html', {'answer': answer})
