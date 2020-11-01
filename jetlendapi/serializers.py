from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions, fields
from rest_auth.models import TokenModel
from rest_auth.utils import import_callable
from jetlendapi.models import UserProfile
from jetlendapi import models

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['id', 'email','name', 'date_of_creation']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_email(self, email, password):
        user = None

        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        user = None

        if username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        user = None

        if email and password:
            user = self.authenticate(email=email, password=password)
        elif username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include either "username" or "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            elif app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    email_address.send_confirmation(
                        request=self.context.get('request')
                    )
                    raise serializers.ValidationError(_('E-mail is not verified.'))

        attrs['user'] = user
        return attrs

class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model.
    """

    class Meta:
        model = TokenModel
        fields = ('key',)


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = UserModel
        fields = ('pk', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('email', )


class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """
    token = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        """
        Required to allow using custom USER_DETAILS_SERIALIZER in
        JWTSerializer. Defining it here to avoid circular imports
        """
        rest_auth_serializers = getattr(settings, 'REST_AUTH_SERIALIZERS', {})
        JWTUserDetailsSerializer = import_callable(
            rest_auth_serializers.get('USER_DETAILS_SERIALIZER', UserDetailsSerializer)
        )
        user_data = JWTUserDetailsSerializer(obj['user'], context=self.context).data
        return user_data

''' сериализатор картинки '''

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PassportImage
        fields = ('passport_file', )

''' Сериализатор основной формы '''

class IdentifierSerializer(serializers.ModelSerializer):
    birth = fields.DateTimeField(format='%d/%m/%Y', required=True)
    dateofissue = fields.DateTimeField(format='%d/%m/%Y', required=True)
    images = ImageSerializer(many=True, read_only=True)
    surname = fields.CharField(required=True)
    name = fields.CharField(required=True)
    patronymic = fields.CharField(required=True)
    passport = fields.IntegerField(required=True)
    districtcode = fields.IntegerField(required=True)
    districtname = fields.CharField(required=True)
    address = fields.CharField(required=True)

    class Meta:
        model = models.Identifier
        fields = ('id', 'surname', 'name', 'patronymic', 'passport', 'birth',
                  'placeofbirth', 'dateofissue', 'districtcode',
                  'districtname', 'address', 'images')

    def create(self, validated_data):
        images_data = self.context.get('view').request.FILES
        owner_id = self.context['request'].user.id

        if len(list(images_data.values())) > 2:
            raise serializers.ValidationError({
                'images': 'you can add 8 files',
            })

        gallery_identifier = models.Identifier.objects.create(
            surname=validated_data.get('surname'),
            name=validated_data.get('name'), patronymic=validated_data.get('patronymic'),
            passport=validated_data.get('passport'),
            birth=validated_data.get('birth'), owner_id=owner_id, placeofbirth=validated_data.get('placeofbirth'),
            dateofissue=validated_data.get('dateofissue'), districtcode=validated_data.get('districtcode'),
            districtname=validated_data.get('districtname'), address=validated_data.get('address'))
        gallery_identifier.save()

        for image_data in images_data.values():
            models.PassportImage.objects.create(gallery_capsule=gallery_identifier, passport_file=image_data)
        return gallery_identifier

''' сериалиатор галочек '''

class AgreementPolicySerializer(serializers.ModelSerializer):
    rules = fields.BooleanField(required=True)
    tax = fields.BooleanField(required=True)
    agree = fields.BooleanField(required=True)

    class Meta:
        model = models.PolicyAgreement
        fields = ('id', 'rules', 'tax', 'agree')

    def validate(self, data):
        if 'rules' in data and 'tax' in data and 'agree' in data:
            if (data['rules']) is not True:
                raise serializers.ValidationError("rules must be accepted")
            if (data['tax']) is not True:
                raise serializers.ValidationError("tax must be accepted")
            if (data['agree']) is not True:
                raise serializers.ValidationError("agree must be accepted")
            return data

''' Сериализатор галочек 2.0 '''

class AgreementSerializer(serializers.ModelSerializer):
    agrees = AgreementPolicySerializer(many=True)

    class Meta:
        model = models.Identifier
        fields = ('id', 'agrees')

    def update(self, instance, validated_data, partial=True):

        models.PolicyAgreement.objects.create(identifier_related=instance, rules='rules', tax='tax', agree='agree')

        return instance


class CvalificationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CvalificationImage
        fields = ('cvalification_file', )

''' добавление фото '''
class AddCvalificationImgage(serializers.ModelSerializer):
    images = CvalificationImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Identifier
        fields = ('id', 'images')

    def update(self, instance, validated_data, partial=True):
        images_data = self.context.get('view').request.FILES

        if len(list(images_data.values())) > 8:
            raise serializers.ValidationError({
                'images': 'you can add 1 file',
            })

        for image_data in images_data.values():
            models.PassportImage.objects.create(gallery_cvalification=instance, cvalification_file=image_data)

        return instance

