from django.db import models

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    year_of_experience = models.IntegerField()

    def __str__(self):
        return self.name