from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_auth.app_settings import (
    TokenSerializer, LoginSerializer,
    JWTSerializer, create_token
)
from rest_framework.response import Response
from rest_auth.utils import jwt_encode
from django.utils.decorators import method_decorator
from rest_framework.generics import GenericAPIView
from rest_auth.models import TokenModel
from jetlendapi import serializers, models
from django.conf import settings
from django.contrib.auth import (
    login as django_login,
)
from django.views.decorators.debug import sensitive_post_parameters
sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password', 'old_password', 'new_password1', 'new_password2'
    )
)

class LoginView(GenericAPIView):
    """
    Check the credentials and return the REST Token
    if the credentials are valid and authenticated.
    Calls Django Auth login method to register User ID
    in Django session framework

    Accept the following POST parameters: username, password
    Return the REST Framework Token Object's key.
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    token_model = TokenModel

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def process_login(self):
        django_login(self.request, self.user)

    def get_response_serializer(self):
        if getattr(settings, 'REST_USE_JWT', False):
            response_serializer = JWTSerializer
        else:
            response_serializer = TokenSerializer
        return response_serializer

    def login(self):
        self.user = self.serializer.validated_data['user']

        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(self.user)
        else:
            self.token = create_token(self.token_model, self.user,
                                      self.serializer)

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()

    def get_response(self):
        serializer_class = self.get_response_serializer()

        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': self.user,
                'token': self.token
            }
            serializer = serializer_class(instance=data,
                                          context={'request': self.request})
        else:
            serializer = serializer_class(instance=self.token,
                                          context={'request': self.request})

        response = Response(serializer.data, status=status.HTTP_200_OK)
        if getattr(settings, 'REST_USE_JWT', False):
            from rest_framework_jwt.settings import api_settings as jwt_settings
            if jwt_settings.JWT_AUTH_COOKIE:
                from datetime import datetime
                expiration = (datetime.utcnow() + jwt_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(jwt_settings.JWT_AUTH_COOKIE,
                                    self.token,
                                    expires=expiration,
                                    httponly=True)
        return response

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data,
                                              context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()


class IdentifierCreateAPIView(generics.CreateAPIView):
    queryset = models.Identifier.objects.all()
    serializer_class = serializers.IdentifierSerializer
    permission_classes = (IsAuthenticated, )


class AgreementView(generics.UpdateAPIView):

    serializer_class = serializers.AgreementSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return models.Identifier.objects.filter(owner=self.request.user)

class AddCvalification(generics.UpdateAPIView):

    serializer_class = serializers.AddCvalificationImgage
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return models.Identifier.objects.filter(owner=self.request.user)
