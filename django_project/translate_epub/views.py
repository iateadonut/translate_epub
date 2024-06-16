from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    # Add any necessary logic for the home view
    return render(request, 'translate_epub/home.html')
