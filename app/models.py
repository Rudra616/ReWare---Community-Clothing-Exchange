from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# ------------------------
# Custom User Model
# ------------------------

class CustomUser(AbstractUser):
    points = models.IntegerField(default=0)  # For point-based system
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    reset_token = models.UUIDField(null=True, blank=True)
    reset_expire = models.DateTimeField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)  # ✅ kept only one

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    district = models.ForeignKey('District', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')  # ✅ added related_name
    state = models.ForeignKey('State', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')      # ✅ added related_name
    email_verification_token = models.CharField(
    max_length=100, unique=True, blank=True, null=True, default=uuid.uuid4)

    def __str__(self):
        return self.username

# ------------------------
# Item Model
# ------------------------

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('Men', 'Men'),
        ('Women', 'Women'),
        ('Kids', 'Kids'),
        ('Other', 'Other'),
    ]

    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Like New', 'Like New'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    size = models.CharField(max_length=50, help_text="e.g., S, M, L, XL ,XXL or numeric")
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    image = models.ImageField(upload_to='items/')
    approved = models.BooleanField(default=False)  # Admin approval required
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.owner.username})"

    def is_available(self):
        return not self.swaps.filter(status__in=['Pending', 'Accepted']).exists()

# ------------------------
# Swap Model
# ------------------------

class Swap(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),   # Initial request
        ('Accepted', 'Accepted'), # Admin acceptance
        ('Rejected', 'Rejected'), # Admin rejection
        ('Completed', 'Completed'), # After successful swap
        ('Cancelled', 'Cancelled'), # If user cancels the swap
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='swaps')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='swaps')
    points_used = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Swap: {self.user.username} → {self.item.title} [{self.status}]"

# ------------------------
# Admin Review Model
# ------------------------

class AdminReview(models.Model):
    admin = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='moderations')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=[('Approved', 'Approved'), ('Rejected', 'Rejected')])
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} {self.action} {self.item.title} at {self.timestamp}"

# ------------------------
# State and District Models
# ------------------------

class State(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=50)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
