from django.urls import path
from . import views

app_name = 'Administrator'

urlpatterns = [

    # Admin Dashboard
    path(
        'AdminDashboard/',
        views.AdminDashboard,
        name='AdminDashboard'
    ),

    # Manage Users
    path(
        'ManageUser/',
        views.ManageUser,
        name='ManageUser'
    ),

    # Manage Doctors
    path(
        'ManageDoctor/',
        views.ManageDoctor,
        name='ManageDoctor'
    ),

    # Pregnancy Milestones
    path(
        'ManageMilestones/',
        views.ManageMilestones,
        name='ManageMilestones'
    ),

    # Nutrition
    path(
        'ManageNutrition/',
        views.ManageNutrition,
        name='ManageNutrition'
    ),

    # Medicines
    path(
        'ManageMedicines/',
        views.ManageMedicines,
        name='ManageMedicines'
    ),

    # Reports
    path(
        'Reports/',
        views.Reports,
        name='Reports'
    ),

    # Dataset Upload
    path(
        'UploadDataset/',
        views.UploadDataset,
        name='UploadDataset'
    ),

    # ChatBox
    path(
        'ChatBox/',
        views.ChatBox,
        name='ChatBox'
    ),
]