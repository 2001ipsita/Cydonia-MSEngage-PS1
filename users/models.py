from django.db import models
from django.contrib.auth.models import User
import os
import datetime
# Create your models here.
class Profile(models.Model):
    staff = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    address = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=50,null=True)
    image = models.ImageField(default="download.png" ,
                              upload_to='profile_images')

    def __str__(self):
        return f'{self.staff.username}-Profile'
	

class Present(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE)
	date = models.DateField(default=datetime.date.today)
	present=models.BooleanField(default=False)
	
class Time(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE)
	date = models.DateField(default=datetime.date.today)
	time=models.DateTimeField(null=True,blank=True)
	out=models.BooleanField(default=False)
	
class Dataset(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    sample=models.CharField(max_length=200,default="0")
    is_sampleUploaded=models.BooleanField(default=False)
    is_trained=models.BooleanField(default=False)
    @property
    def is_deleted(self):
        Name=self.user.username
        if(os.path.exists('faceRecognition_data/training_dataset/{}/'.format(Name))==False):
            return True
        else:
            return False