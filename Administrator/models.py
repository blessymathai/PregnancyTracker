from django.db import models

class tbl_Milestone(models.Model):
    week = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    tips = models.TextField(blank=True)

    class Meta:
        db_table = 'tbl_Milestone'
        ordering = ['week']

    def __str__(self):
        return self.title

class tbl_Nutrition(models.Model):

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    week_start = models.PositiveIntegerField(default=1)
    week_end = models.PositiveIntegerField(default=40)
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    iron = models.FloatField(default=0)
    calcium = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    recommendation = models.TextField(blank=True)

    class Meta:
        db_table = 'tbl_Nutrition'

    def __str__(self):
        return self.name

# class tbl_Nutrition(models.Model):
#     name = models.CharField(max_length=150)
#     category = models.CharField(max_length=100, blank=True)
#     calories = models.FloatField(default=0)
#     protein = models.FloatField(default=0)
#     iron = models.FloatField(default=0)
#     calcium = models.FloatField(default=0)
#     fiber = models.FloatField(default=0)
#     recommendation = models.TextField(blank=True)

#     class Meta:
#         db_table = 'tbl_Nutrition'
#         ordering = ['name']

#     def __str__(self):
#         return self.name


class tbl_Medicine(models.Model):
    name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100, blank=True)
    purpose = models.TextField(blank=True)
    warning = models.TextField(blank=True)

    class Meta:
        db_table = 'tbl_Medicine'

    def __str__(self):
        return self.name


class tbl_Dataset(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    rows = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'tbl_Dataset'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name
