from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    content = models.TextField(null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank=True,related_name='sent_messages')
    recipient = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='received_messages')
    created_at = models.DateTimeField(auto_now_add=True)