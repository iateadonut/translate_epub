"""
URL configuration for translate_epub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('translate_book/<int:book_id>/<int:language_id>/', views.translate_book, name='translate_book'),
    path('', views.home, name='home'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/ask_question/', views.ask_question, name='ask_question'),
    path('book_item/<int:item_id>/', views.book_item_detail, name='book_item_detail'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    path('update_element/<int:element_id>/', views.update_element, name='update_element'),
]
