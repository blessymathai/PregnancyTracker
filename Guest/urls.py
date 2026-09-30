from django.urls import path
from Guest import views

app_name = 'Guest'

urlpatterns = [

    path('', views.HomePage, name='HomePage'),

    path('Login/', views.Login, name='Login'),

    path('UserRegistration/',
         views.UserRegistration,
         name='UserRegistration'),

    path('Logout/',
         views.Logout,
         name='Logout'),

    path('DoctorLogin/',
         views.DoctorLogin,
         name='DoctorLogin'),

    path('AdminLogin/',
         views.AdminLogin,
         name='AdminLogin'),
]