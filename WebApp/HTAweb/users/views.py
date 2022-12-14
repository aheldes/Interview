from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


# Create your views here.



def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('main:home')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            return redirect('main:home')
        else:
            messages.error(request,"Invalid username or password.")
            return render(request, 'main/home.html')
    else:
        return render(request, 'users/login.html')

def logout_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('users:login')
    logout(request)
    return redirect('main:home')