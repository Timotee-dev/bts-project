from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.models import Order, Wishlist
from .models import Customer
from .forms import ProfileUpdateForm


def register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'vendor'):
            return redirect('vendor_dashboard')
        return redirect('dashboard')

    errors = {}

    if request.method == 'POST':
        account_type  = request.POST.get('account_type', 'shopper')
        first_name    = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        email         = request.POST.get('email', '').strip()
        username      = request.POST.get('username', '').strip()
        phone         = request.POST.get('phone', '').strip()
        university    = request.POST.get('university', '').strip()
        password1     = request.POST.get('password1', '')
        password2     = request.POST.get('password2', '')

        # Validate
        if not username:
            errors['username'] = 'Username is required.'
        elif Customer.objects.filter(username=username).exists():
            errors['username'] = 'That username is already taken.'

        if not email:
            errors['email'] = 'Email is required.'
        elif Customer.objects.filter(email=email).exists():
            errors['email'] = 'An account with that email already exists.'

        if not password1:
            errors['password1'] = 'Password is required.'
        elif len(password1) < 8:
            errors['password1'] = 'Password must be at least 8 characters.'
        elif password1 != password2:
            errors['password2'] = 'Passwords do not match.'

        if not first_name:
            errors['first_name'] = 'First name is required.'

        if not errors:
            user = Customer.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                university=university,
            )

            if account_type == 'vendor':
                from vendors.models import Vendor
                business_name  = request.POST.get('business_name', username)
                business_email = request.POST.get('business_email', email)
                Vendor.objects.create(
                    user=user,
                    business_name=business_name,
                    phone=phone,
                    email=business_email,
                    description=request.POST.get('description', ''),
                    bank_name=request.POST.get('bank_name', ''),
                    account_number=request.POST.get('account_number', ''),
                    account_name=request.POST.get('account_name', ''),
                )
                messages.success(request, f'Vendor store "{business_name}" created! Sign in below.')
            else:
                messages.success(request, f'Welcome to BTS, {first_name}! Sign in below.')

            return redirect('login')

    return render(request, 'accounts/register.html', {
        'errors': errors,
        'account_type': request.POST.get('account_type', '') if request.method == 'POST' else '',
        'post_data': request.POST if request.method == 'POST' else {},
    })


def user_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'vendor'):
            return redirect('vendor_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            if hasattr(user, 'vendor'):
                return redirect('vendor_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'accounts/login.html', {})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    recent_orders = Order.objects.filter(customer=request.user)[:5]
    wishlist, _ = Wishlist.objects.get_or_create(customer=request.user)
    return render(request, 'accounts/dashboard.html', {
        'recent_orders': recent_orders,
        'wishlist': wishlist,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})