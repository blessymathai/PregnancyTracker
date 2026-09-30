from django.urls import path
from User import views
app_name='User'
urlpatterns = [
    path('UserDashboard/', views.UserDashboard, name='UserDashboard'),
    path('PregnancyProfile/', views.PregnancyProfile, name='PregnancyProfile'),
    path('PregnancyTracker/', views.PregnancyTracker, name='PregnancyTracker'),
    path('WeeklyRecordHistory/', views.WeeklyRecordHistory, name='WeeklyRecordHistory'),
    path('BabyGrowth/', views.BabyGrowth, name='BabyGrowth'),
    path('Nutrition/', views.Nutrition, name='Nutrition'),
    path('Appointments/', views.Appointments, name='Appointments'),
    path('Messages/', views.Messages, name='Messages'),
    path('Profile/', views.Profile, name='Profile'),
    path('MyProfile/', views.MyProfile, name='MyProfile'),
    path('AIPrediction/',views.AIPrediction,name='AIPrediction'),
    path('AIPredictionValues/', views.AIPredictionValues, name='AIPredictionValues'),
    path('AIChatbot/', views.AIChatbot, name='AIChatbot'),
    # path('predict/', views.predict_health_risk, name='predict_health_risk'),
]