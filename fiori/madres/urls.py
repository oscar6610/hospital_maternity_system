"""
URLs para la app Fiori de Madres
"""
from django.urls import path
from . import views

app_name = 'madres'

urlpatterns = [
    # Vista principal de lista de madres
    path('list/', views.madres_list, name='list'),
    
    # Vista de creación de madre
    path('create/', views.madres_create, name='create'),
    
    # Vista de detalle de madre
    path('<int:id_madre>/', views.madres_detail, name='detail'),
    
    # Vista de edición
    path('<int:id_madre>/edit/', views.madres_edit, name='edit'),
    
    # Vista de embarazos de una madre
    path('<int:id_madre>/embarazos/', views.madres_embarazos, name='embarazos'),
    
    # Vista de partos de una madre
    path('<int:id_madre>/partos/', views.madres_partos, name='partos'),
    
    # Vista de atenciones IVE
    path('ive/', views.ive_list, name='ive-list'),
]