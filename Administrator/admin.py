# Register your models here.
from django.contrib import admin
from .models import tbl_Milestone,tbl_Nutrition,tbl_Medicine,tbl_Dataset
admin.site.register([tbl_Milestone,tbl_Nutrition,tbl_Medicine,tbl_Dataset])
