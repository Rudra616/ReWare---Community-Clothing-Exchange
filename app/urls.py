from django.urls import path, include
from .views import *
urlpatterns = [
    path('login/', login_view, name='login'),  # 👈 Added login
    path('logout/', logout_view, name='logout'),
    path('swap/<int:swap_id>/<str:action>/', review_swap, name='review_swap'),
    path('item/<int:item_id>/send-request/',send_swap_request, name='send_swap_request'),
    path('complete_swap/', complete_swap, name='complete_swap'),

    path("refresh_captcha/", refresh_captcha, name="refresh_captcha"),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/<uuid:token>/',reset_password_view, name='reset_password'),
    path('browse-items/', browse_items, name='browse_items'),
    path('item/<int:item_id>/', item_detail, name='item_detail'),
    path('item/<int:item_id>/request-swap/',request_swap, name='request_swap'),
    path('item/<int:item_id>/redeem-points/', redeem_points, name='redeem_points'),
    path('add-item/', add_item, name='add_item'),
    path('dashboard/', login_required(user_dashboard), name='user_dashboard'),
    path('delete-item/<int:item_id>/', login_required(delete_item), name='delete_item'),
    path('',index, name='index'),  # Home page URL named 'index'
    path('about/',about_view, name='about'),  # About
    path('register/', register, name='register'),
    path('verify/<uuid:token>/',verify_email, name='verify_email'),
    path('contact/', contact_view, name='contact'),  # 👈 This is missing
    path('update-profile/', update_profile, name='update_profile'),

]   
