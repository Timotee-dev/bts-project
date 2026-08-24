from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.models import Order, Wishlist
from .models import Customer
from .forms import CustomerRegistrationForm, CustomerLoginForm, ProfileUpdateForm


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        account_type = request.POST.get('account_type', 'shopper')
        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            if account_type == 'vendor':
                # Create vendor profile immediately from the extra fields
                from vendors.models import Vendor
                Vendor.objects.create(
                    user=user,
                    business_name=request.POST.get('business_name', user.get_full_name() or user.username),
                    phone=request.POST.get('phone', ''),
                    email=request.POST.get('business_email', user.email),
                    description=request.POST.get('description', ''),
                    bank_name=request.POST.get('bank_name', ''),
                    account_number=request.POST.get('account_number', ''),
                    account_name=request.POST.get('account_name', ''),
                )
                messages.success(request, f'Welcome! Your vendor store is live. Add your first product to get started.')
                return redirect('vendor_dashboard')
            else:
                messages.success(request, f'Welcome to BTS, {user.first_name}! Start shopping.')
                return redirect('dashboard')
        else:
            # Re-render with errors — pass account_type so JS can re-open correct form
            return render(request, 'accounts/register.html', {
                'form': form,
                'account_type': request.POST.get('account_type', 'shopper'),
            })

    form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'vendor'):
            return redirect('vendor_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            # Send vendors to vendor dashboard, shoppers to customer dashboard
            if hasattr(user, 'vendor'):
                return redirect('vendor_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomerLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


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
    from django.shortcuts import get_object_or_404
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})
