from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def register (request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect("home")
            return redirect("users:login")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {'form': form})

# Create your views here.
def login_view (request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('users:login')
    
    return redirect('home')
