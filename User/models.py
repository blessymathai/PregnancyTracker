from django.db import models
from django.contrib.auth.models import User
from Guest.models import tbl_registration
from django.utils import timezone
# Create your models here.

class tbl_UserProfile(models.Model):
    user = models.ForeignKey(tbl_registration, on_delete=models.CASCADE, null=True, blank=True, related_name='user_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    class Meta:
        db_table = 'tbl_UserProfile'

    def __str__(self):
        return self.user.user_name if self.user else f"Profile {self.id}"

class tbl_AIChatMessage(models.Model):
    user = models.ForeignKey(tbl_registration, on_delete=models.CASCADE, related_name='ai_chats')
    sender = models.CharField(max_length=20, default='USER')  # 'USER' or 'BOT'
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_AIChatMessage'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.user_name} ({self.sender}): {self.message[:30]}"

class tbl_PregnancyTracker(models.Model):
    user = models.ForeignKey(tbl_registration, on_delete=models.CASCADE, related_name='pregnancy_records')
    last_period_date = models.DateField()
    expected_delivery_date = models.DateField()
    current_week = models.PositiveIntegerField(default=1)
    weight = models.FloatField(null=True, blank=True)
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_PregnancyTracker'
        ordering = ['-updated_at']

    @property
    def current_month(self):
        return max(1, min(10, (self.current_week - 1) // 4 + 1))

    def __str__(self):
        return f"{self.user.user_name} - Week {self.current_week}"

class tbl_PregnancyWeeklyRecord(models.Model):
    pregnancy = models.ForeignKey(tbl_PregnancyTracker, on_delete=models.CASCADE, related_name='weekly_records')
    week = models.PositiveIntegerField()
    weight = models.FloatField(null=True, blank=True)
    symptoms = models.TextField(blank=True)
    mood = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_PregnancyWeeklyRecord'
        ordering = ['-week', '-recorded_at']

class tbl_Baby(models.Model):
    user = models.ForeignKey(tbl_registration, on_delete=models.CASCADE, related_name='babies')
    baby_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    birth_weight = models.FloatField(null=True, blank=True)
    current_weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_Baby'
        ordering = ['-id']
