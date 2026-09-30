# Register your models here.
from django.contrib import admin
from .models import tbl_UserProfile,tbl_PregnancyTracker,tbl_PregnancyWeeklyRecord,tbl_Baby
admin.site.register([tbl_UserProfile,tbl_PregnancyTracker,tbl_PregnancyWeeklyRecord,tbl_Baby])