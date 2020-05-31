from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.


class UserInfo(AbstractUser):
    company = models.CharField(max_length=32)
    auth = models.IntegerField()
    name = models.CharField(max_length=32)
    record_time = models.DateField(default=None)


class Diary(models.Model):
    id = models.AutoField(primary_key=True)
    info = models.CharField(max_length=150)
    record_time = models.DateField()


class Operation_record(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=32)
    operation_code=models.IntegerField()
    record_time = models.DateTimeField(default=None)
    picture=models.ImageField(upload_to ='media')
    website=models.CharField(max_length=256)


class All_Bird(models.Model):
    sci_name=models.CharField(max_length=256,primary_key=True)
    name=models.CharField(max_length=256)
    pos=models.CharField(max_length=256)
