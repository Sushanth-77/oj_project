from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.info(request, 'Username and password are required')
            return redirect("/auth/register/")

        if User.objects.filter(username=username).exists():
            messages.info(request, 'User with this username already exists')
            return redirect("/auth/register/")
        
        User.objects.create_user(username=username, password=password)
        messages.info(request, 'User created successfully. Please login.')
        return redirect('/auth/login/')  # Redirect to login after registration

    return render(request, 'register.html')

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.info(request, 'Username and password are required')
            return redirect('/auth/login/')

        if not User.objects.filter(username=username).exists():
            messages.info(request, 'User with this username does not exist')
            return redirect('/auth/login/')
        
        user = authenticate(username=username, password=password)

        if user is None:
            messages.info(request, 'Invalid password')
            return redirect('/auth/login/')
        
        login(request, user)
        messages.info(request, 'Login successful')
        return redirect('/home/polls/')
    
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    messages.info(request,'logout successful')
    return redirect('/auth/login/')
