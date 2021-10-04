from django.db import models

# Create your models here.
class User(models.Model):
    # Required fields
    id = models.CharField(max_length=128, primary_key=True) # sub in Auth0 user info
    username = models.CharField(max_length=32) # nickname in Auth0 user info
    email = models.EmailField(max_length=32) # email does not need to be unique, social login can have the same email, auth0 will handle it
    # Optional fields
    firstname = models.CharField(max_length=32, blank=True)
    lastname = models.CharField(max_length=32, blank=True)
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('N', 'Not Selected')
    )
    gender = models.CharField(max_length=1, choices=GENDERS, default='N')
    birthday = models.DateField(blank=True, null=True)
    picture = models.URLField(max_length=1024, blank=True)
    encouragement = models.TextField(max_length=256, blank=True, default='Perseverance, secret of all triumphs - Victor Hugo (Edit this to be anything you want in Profile -> Motivation)')
    subscribed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Goal(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=1024, blank=True)
    deadline = models.DateField(blank=True, null=True)
    picture = models.URLField(max_length=1024, blank=True)
    category_id = models.ForeignKey('Category', on_delete=models.CASCADE, default=1)
    complete = models.BooleanField(default=False)
    completion_date = models.DateField(blank=True, null=True)
    current_steps_count = models.IntegerField(default=0)
    total_steps_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Step(models.Model):
    id = models.BigAutoField(primary_key=True)
    goal_id = models.ForeignKey(Goal, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=1024, blank=True)
    deadline = models.DateField(null=True)
    recurring = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    completion_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    picture = models.URLField(max_length=1024, blank=True)
    description = models.TextField(max_length=128, blank=True)