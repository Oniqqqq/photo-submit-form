from datetime import datetime

from django.core.management import BaseCommand
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractUser

from jetlend import settings


class UserProfileManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, name, password=None):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('Please enter an email')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        Create and save a SuperUser with the given email and password.
        """
        user = self.create_user(email, name, password)

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    date_of_creation = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', ]

    objects = UserProfileManager()

    def get_full_name(self):
        return self.name

    def __str__(self):
        return self.email

def get_deleted_user():
    return settings.AUTH_USER_MODEL.objects.get_or_create(username='deleted')[0]

''' основные данные пользователя '''

class Identifier(models.Model):
    PLACES = (
        ('Msc', 'Moscow'),
        ('Spb', 'Saint-Petersburg'),
        ('Ufa', 'Ufa'),
        ('Alb', 'Albuquerque'),
        ('Frg', 'Fargo'),
        ('etc', 'etc.')
    )

    surname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    patronymic = models.CharField(max_length=255)
    passport = models.IntegerField()
    birth = models.DateField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owner_user', on_delete=models.SET(get_deleted_user), default=1)
    placeofbirth = models.CharField(max_length=32, choices=PLACES, default='Msc')
    dateofissue = models.DateField()
    districtcode = models.IntegerField()
    districtname = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

''' Фото паспорта '''

class PassportImage(models.Model):
    passport_file = models.FileField(blank=True, null=True,
                                    upload_to='media/covers/%Y/%m/%D/')
    gallery_passport = models.ForeignKey(Identifier, related_name='images', on_delete=models.CASCADE)

''' Галочки на согласие с правилами '''

class PolicyAgreement(models.Model):
    rules = models.BooleanField(default=False)
    tax = models.BooleanField(default=False)
    agree = models.BooleanField(default=False)
    identifier_related = models.ForeignKey(Identifier, related_name='agreement', on_delete=models.CASCADE)

''' Картинка на добавление квалификации '''

class CvalificationImage(models.Model):
    cvalification_file = models.FileField(blank=True, null=True,
                                    upload_to='media/covers/%Y/%m/%D/')
    gallery_cvalification = models.ForeignKey(Identifier, related_name='cvals', on_delete=models.CASCADE)



