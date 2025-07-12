from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import logout

from django.contrib.auth import authenticate, login as auth_login
from .models import *
from django.template.loader import render_to_string  # for rendering template to string
from django.core.paginator import Paginator
from django.http import JsonResponse
import random
from django.core.mail import send_mail
from django.conf import settings
import uuid

from django.http import JsonResponse
def generate_captcha():
    """Generate a random 4-digit captcha code"""
    return str(random.randint(1000, 9999))

def refresh_captcha(request):
    new_captcha = generate_captcha()
    request.session['captcha_code'] = new_captcha
    return JsonResponse({'captcha_code': new_captcha})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('name')
        password = request.POST.get('password')
        entered_captcha = request.POST.get('captcha')
        saved_captcha = request.session.get('captcha_code')

        if entered_captcha != saved_captcha:
            new_captcha = generate_captcha()
            request.session['captcha_code'] = new_captcha
            return render(request, 'login.html', {
                'error': 'Invalid captcha. Try again.',
                'captcha_code': new_captcha,
            })

        user_obj = CustomUser.objects.filter(username=username).first()

        if user_obj:
            if user_obj.check_password(password):
                if not user_obj.is_active:
                    return render(request, 'login.html', {
                        'error3': 'Please verify your email first.',
                        'captcha_code': saved_captcha,
                    })
                auth_login(request, user_obj)
                return redirect('index')
            else:
                return render(request, 'login.html', {
                    'error': 'Wrong password',
                    'captcha_code': saved_captcha,
                })
        else:
            return render(request, 'login.html', {
                'error1': 'Username not found',
                'captcha_code': saved_captcha,
            })

    # GET request
    captcha_code = generate_captcha()
    request.session['captcha_code'] = captcha_code
    return render(request, 'login.html', {'captcha_code': captcha_code})

def forgot_password_view(request):
    message = ""
    if request.method == 'POST':
        username = request.POST.get('username')
        User = CustomUser.objects.filter(username=username).first()
        if User:
            token = uuid.uuid4()
            User.reset_token = token
            User.reset_expire = timezone.now() + timezone.timedelta(hours=1)
            User.save()
            reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
            send_mail(
                'Password Reset',
                f'Reset your password using this link: {reset_link}',
                settings.EMAIL_HOST_USER,
                [User.email],
                fail_silently=False,
            )
        # Show message regardless of username validity
        message = "If the username exists, a reset link has been sent to the registered email."

    return render(request, 'forgot_password.html', {'message': message})
from django.utils import timezone
def reset_password_view(request, token):
    User = get_object_or_404(CustomUser, reset_token=token, reset_expire__gt=timezone.now())
    # get_object_or_404 work like try catch excpetion
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password == confirm:
            User.password = password  
            User.reset_token = None
            User.reset_expire = None
            User.save()
            return redirect('login')
        else:
            return render(request, 'reset_password.html', {'error': 'Passwords do not match.'})

    return render(request, 'reset_password.html')


def logout_view(request):
    logout(request)
    return redirect('login')

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from .models import Item

def browse_items(request):
    items = Item.objects.filter(approved=True).order_by('-id')  # Only approved items
    paginator = Paginator(items, 8)  # 8 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render(request, 'partials/items_list.html', {'page_obj': page_obj}).content.decode('utf-8')
        return JsonResponse({'html': html, 'has_next': page_obj.has_next()})

    return render(request, 'browse_items.html', {'page_obj': page_obj})

def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id, approved=True)  # Only approved items
    return render(request, 'item_detail.html', {'item': item})

@login_required
def request_swap(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Item, pk=item_id, approved=True)
        user = request.user
        # Check availability and create swap request
        if item.is_available():
            Swap.objects.create(user=user, item=item, points_used=0, status='Pending')
            return JsonResponse({'message': 'Swap request sent successfully!'})
        else:
            return JsonResponse({'message': 'Item not available for swapping.'}, status=400)
    return JsonResponse({'message': 'Invalid request method.'}, status=405)

@login_required
def redeem_points(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Item, pk=item_id, approved=True)
        user = request.user
        points_required = 10  # Example fixed points cost; you can extend your model for variable costs
        if user.points >= points_required and item.is_available():
            # Deduct points and create swap with points
            user.points -= points_required
            user.save()
            Swap.objects.create(user=user, item=item, points_used=points_required, status='Pending')
            return JsonResponse({'message': f'You redeemed {points_required} points for this item!'})
        else:
            return JsonResponse({'message': 'Not enough points or item not available.'}, status=400)
    return JsonResponse({'message': 'Invalid request method.'}, status=405)



@login_required
@login_required
def add_item(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            size = request.POST.get('size')
            condition = request.POST.get('condition')
            image = request.FILES.get('image')

            if not all([title, description, category, size, condition, image]):
                return JsonResponse({'success': False, 'message': 'All fields are required.'})

            valid_categories = dict(Item.CATEGORY_CHOICES).keys()
            valid_conditions = dict(Item.CONDITION_CHOICES).keys()

            if category not in valid_categories or condition not in valid_conditions:
                return JsonResponse({'success': False, 'message': 'Invalid category or condition selected.'})

            item = Item.objects.create(
                owner=request.user,
                title=title,
                description=description,
                category=category,
                size=size,
                condition=condition,
                image=image,
                approved=False,
            )
            return JsonResponse({'success': True, 'message': 'Item added successfully! Waiting for approval.'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})

    context = {
        'category_choices': Item.CATEGORY_CHOICES,
        'condition_choices': Item.CONDITION_CHOICES,
    }
    return render(request, 'add_item.html', context)

@login_required
def user_dashboard(request):
    my_items = Item.objects.filter(owner=request.user)
    sent_swaps = Swap.objects.filter(user=request.user)
    received_swaps = Swap.objects.filter(item__owner=request.user)

    return render(request, 'user_dashboard.html', {
        'my_items': my_items,
        'sent_swaps': sent_swaps,
        'received_swaps': received_swaps
    })

from django.contrib.auth.decorators import login_required




@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('update_profile')

    return render(request, 'update_profile.html', {'user': request.user})


def contact_view(request):
    return render(request, 'contact.html')

@login_required
@csrf_exempt  # because using AJAX POST, or add CSRF token header properly
def delete_item(request, item_id):
    if request.method == 'POST':
        try:
            item = Item.objects.get(id=item_id, owner=request.user)
            item.delete()
            return JsonResponse({'success': True})
        except Item.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
from django.shortcuts import render

def index(request):
    items_list = Item.objects.filter(approved=True).order_by('-created_at')
    paginator = Paginator(items_list, 9)
    page_number = request.GET.get('page', 1)
    items = paginator.get_page(page_number)
    return render(request, 'index.html', {'items': items})

def about_view(request):

    return render(request, 'about.html')
from datetime import datetime
def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
            number = request.POST.get('number', '').strip()
            firstname = request.POST.get('firstname', '').strip()
            lastname = request.POST.get('lastname', '').strip()
            address = request.POST.get('address', '').strip()
            date_of_birth_str = request.POST.get('date_of_birth', '').strip()
            bio = request.POST.get('bio', '').strip()
            profile_image = request.FILES.get('profile_image')

            # Validate required fields
            if not all([username, password, email, number, firstname, lastname, address, date_of_birth_str]):
                return JsonResponse({'success': False, 'message': 'All fields are required.'})

            # Convert DOB
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format for date of birth.'})

            # Check duplicates
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already taken.'})
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already registered.'})

            # Create user
            token = uuid.uuid4()
            user = CustomUser(
                first_name=firstname,
                last_name=lastname,
                username=username,
                email=email,
                phone_number=number,
                address=address,
                date_of_birth=date_of_birth,
                bio=bio,
                profile_image=profile_image,
                email_verification_token=token,
                is_active=False
            )
            user.set_password(password)
            user.save()

            # Send verification email
            verification_link = request.build_absolute_uri(f'/verify/{token}/')
            html_content = render_to_string("email.html", {'verificationtoken': verification_link})
            plain_text = strip_tags(html_content)

            email_subject = 'Verify your ReWear Account'
            from_email = settings.EMAIL_HOST_USER
            to_email = [user.email]

            email_msg = EmailMultiAlternatives(email_subject, plain_text, from_email, to_email)
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send(fail_silently=False)

            return JsonResponse({'success': True, 'message': 'Registration successful. Please check your email to verify your account.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Internal server error: {str(e)}'}, status=500)

    # ✅ Handle GET request — show the registration page
    return render(request, 'register.html')
def verify_email(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        if user.is_active:
            # Already verified
            messages.info(request, "Email already verified. Please login.")
        else:
            # Verify email
            user.is_active = True
            user.email_verification_token = None  # clear token after verification
            user.save()
            messages.success(request, "Email verified successfully! Please login.")
        return redirect('login')  # replace 'login' with your login url name
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid or expired verification link.")
        return redirect('login')




@login_required
def review_swap(request, swap_id, action):
    swap = get_object_or_404(Swap, id=swap_id, item__uploaded_by=request.user)
    
    if action == 'accept':
        swap.status = 'Accepted'
        # Optional: Mark item as unavailable
        swap.item.approved = False
        swap.item.save()
        messages.success(request, "Swap request accepted.")
    elif action == 'reject':
        swap.status = 'Rejected'
        messages.info(request, "Swap request rejected.")
    else:
        messages.error(request, "Invalid action.")
        return redirect('user_dashboard')

    swap.save()
    return redirect('user_dashboard')

@login_required
def send_swap_request(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Prevent sending request to own item
    if item.owner == request.user:
        messages.error(request, "You can't request your own item.")
        return redirect('item_detail', item_id=item.id)

    # Prevent duplicate pending requests
    if Swap.objects.filter(user=request.user, item=item, status='Pending').exists():
        messages.info(request, "You already sent a request.")
        return redirect('item_detail', item_id=item.id)

    # Create the request
    Swap.objects.create(user=request.user, item=item, status='Pending')
    messages.success(request, "Swap request sent successfully!")
    return redirect('item_detail', item_id=item.id)


@login_required
def review_swap(request, swap_id, action):
    swap = get_object_or_404(Swap, id=swap_id)
    
    if swap.item.uploaded_by != request.user:
        messages.error(request, "You can't respond to this request.")
        return redirect('user_dashboard')

    if action == 'accept':
        swap.status = 'Accepted'
        swap.item.is_available = False  # optional, mark unavailable
        swap.item.save()
    elif action == 'reject':
        swap.status = 'Rejected'
    swap.save()

    messages.success(request, f"Swap request has been {action}ed.")
    return redirect('user_dashboard')

@login_required
def complete_swap(request, swap_id):
    swap = get_object_or_404(Swap, id=swap_id)
    if swap.item.uploaded_by == request.user or swap.user == request.user:
        swap.status = 'Completed'
        swap.save()
        messages.success(request, "Swap marked as completed.")
    return redirect('user_dashboard')

