from django.urls import path, include
from rest_framework.routers import DefaultRouter
from jetlendapi import views
from django.conf.urls import url

urlpatterns = [
    path('agreement/<int:pk>/', views.AgreementView.as_view(), name='agreement'),
    path('cvals/<int:pk>/', views.AddCvalification.as_view(), name='cvals'),

    url(r'identifier/$', views.IdentifierCreateAPIView.as_view(), name='createid'),

]
