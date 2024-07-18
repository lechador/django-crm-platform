from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('finances/', views.finances, name='finances'),
    path('card-usage/', views.card_usage, name="card_usage"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payze-webhook/', views.payze_webhook_gateway, name='payze_webhook_gateway'),
    path('payment-success/', views.success_redirect_gateway, name='payment_success'),
    path('payment-fail/', views.error_redirect_gateway, name='payment_fail'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
    path('cooperative/', views.cooperative, name='cooperative'),
    path('guest/', views.guest, name='guest'),
    path('send_sms/', views.send_recovery_sms, name='send_recovery_sms'),
    path('verify_code/', views.verify_code, name='verify_code'),
    path('update_password/', views.update_password, name='update_password')
]
