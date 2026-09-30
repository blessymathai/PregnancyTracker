from django.db import models

class tbl_registration(models.Model):
    ROLE_CHOICES = (
        ('USER', 'User'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin'),
    )

    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(unique=True)
    user_contact = models.CharField(max_length=20)
    user_address = models.TextField(default='', blank=True)
    user_password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.user_name
