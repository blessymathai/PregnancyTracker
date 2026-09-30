# Register your models here.
from django.contrib import admin
from .models import tbl_Doctor,tbl_Appointment,tbl_Prescription,tbl_Message
admin.site.register([tbl_Doctor,tbl_Appointment,tbl_Prescription,tbl_Message])
