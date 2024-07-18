import calendar
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .models import Balance, Client, CooperativeExpense, SubscriptionType, Cooperative, Subscription, Card, DeviceEvent, Device, Transaction, SubsObserverLog
from .forms import CooperativeExpenseForm, DateRangeForm, PasswordChangeForm
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Sum
from django.db import transaction
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum, Q
import requests
import qrcode
import random
import string
import json
from django.core.files.storage import default_storage
import os

def send_sms(destination, content):
    sms_url = "https://sender.ge/api/send.php"
    params = {
        "apikey": "9be3300ffa6688e040b6981d170d153b",
        "smsno": 2,
        "destination": destination,
        "content": content,
    }

    try:
        response = requests.get(sms_url, params=params)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        # Log error or handle exception
        return False

def initiate_payment(request):
    if request.method == 'POST':
        deposit_amount = request.POST.get('deposit_amount')

        # Construct payload for Payze API
        payload = {
            "source": "card",
            "amount": deposit_amount,
            "currency": "GEL",
            "hooks": {
                "webhookGateway": "http://localhost:8000/payze-webhook",
                "successRedirectGateway": "http://localhost:8000/payment-success",
                "errorRedirectGateway": "http://localhost:8000/payment-fail"
            }
        }

        # Replace 'YOUR_PAYZE_API_KEY' with your actual Payze API key
        headers = {
            'Authorization': 'AB2854F484E145E58C82E9BF2EC91F40:95AA6DC793CA4ADB86FD6C42F6EE02BE',
            'Content-Type': 'application/json'
        }

        url = "https://payze.io/v2/api/payment"

        response = requests.put(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            # Payment initiation successful, redirect user to payment URL
            payment_data = response.json().get('data', {}).get('payment', {})
            transaction_id = payment_data.get('transactionId')  # Extract transactionId

            # Save transactionId to database
            Transaction.objects.create(transaction_id=transaction_id, amount=deposit_amount, status='pending', user=request.user)

            payment_url = payment_data.get('paymentUrl')

            # Redirect user to payment URL
            return redirect(payment_url)
        else:
            # Handle error
            return HttpResponse("Payment initiation failed.")

    return HttpResponse("Invalid request method.")


@csrf_exempt
def payze_webhook_gateway(request):
    if request.method == 'POST':
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)

def success_redirect_gateway(request):
    # Extract transaction ID from request parameters
    transaction_id = request.GET.get('payment_transaction_id')

    if transaction_id:
        try:
            # Retrieve the corresponding transaction from the database
            transaction = Transaction.objects.get(transaction_id=transaction_id)

            # Update the transaction status to "complete"
            transaction.status = 'complete'
            transaction.save()

            # Retrieve the associated user for the transaction
            user = transaction.user

            # Retrieve the user's balance
            balance = Balance.objects.get(user=user)

            # Add the transaction amount to the user's balance
            balance.user_balance += transaction.amount
            balance.save()
            
            # Optionally, perform any additional actions (e.g., redirect user to a success page)
            return redirect("finances")
        except Transaction.DoesNotExist:
            # Handle case where transaction is not found in the database
            return HttpResponse("Transaction not found in the database.")
    else:
        # Handle case where transaction ID is missing from the request parameters
        return HttpResponse("Transaction ID missing from request parameters.")

def error_redirect_gateway(request):
    # Redirect user to error page after failed payment
    return HttpResponse("Redirecting to error page...")

def login_view(request):
    if request.user.is_authenticated:
        if not request.user.password_changed:
            return redirect('change_password')  # Redirect to change password page
        else:
            return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not user.password_changed:
                return redirect('change_password')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'დეტალები არასწორია')
    return render(request, 'login.html')

@login_required
def dashboard(request):
    cooperative = Cooperative.objects.get(id=request.user.cooperative_id)
    cards = Card.objects.filter(temp=False, user_id=request.user.id)
    return render(request, 'dashboard.html', {"cooperative_name": cooperative.cooperative_name, 
                                              "cards": cards})

@login_required
def guest(request):
    return render(request, 'guest.html')

georgian_month_names = {
    'January': 'იანვარი',
    'February': 'თებერვალი',
    'March': 'მარტი',
    'April': 'აპრილი',
    'May': 'მაისი',
    'June': 'ივნისი',
    'July': 'ივლისი',
    'August': 'აგვისტო',
    'September': 'სექტემბერი',
    'October': 'ოქტომბერი',
    'November': 'ნოემბერი',
    'December': 'დეკემბერი',
}

@login_required
def cooperative(request):
    if request.method == 'POST':
        # Handle form submission for adding new cooperative expense
        form = CooperativeExpenseForm(request.POST)
        if form.is_valid():
            form.instance.cooperative_id = request.user.cooperative_id
            form.save()
            messages.success(request, 'ხარჯი წარმატებით აისახა!')
            return redirect('cooperative')
    today = datetime.today()
    last_six_months = [(today - timedelta(days=30 * i)).replace(day=1) for i in range(6)]
    last_six_months.reverse()

    cooperative_id = request.user.cooperative_id
    devices = Device.objects.filter(cooperative_id=cooperative_id)
    cooperative = Cooperative.objects.get(pk=cooperative_id)
    cooperative_price = cooperative.cooperative_device_price
    # ეს არის მთლიანი პერიოდის
    total_event_count = DeviceEvent.objects.filter(
        device_id__in=devices,
        processed=True,
        event_type=0,
    ).exclude(Q(payed="sub"))

    total_event_sum = total_event_count.aggregate(event_sum=Sum('payed'))['event_sum'] or 0


    total_subscriptions = Subscription.objects.filter(
        cooperative_id=cooperative_id,
    )
    total_subscription_price = total_subscriptions.aggregate(total_price=Sum('price'))['total_price'] or 0

    full_total_expenses = CooperativeExpense.objects.filter(
        cooperative_id=cooperative_id
    )
    sum_total_expenses = full_total_expenses.aggregate(total_expenses=Sum('amount'))['total_expenses'] or 0
    cooperative_balance = round((float(total_event_sum) + float(total_subscription_price) - float(sum_total_expenses)),1)
    # აქამდე

    tab_data = []
    for month in last_six_months:
        start_date = month
        end_date = start_date.replace(day=calendar.monthrange(month.year, month.month)[1])
        print(start_date)
        print(end_date)
        expenses = CooperativeExpense.objects.filter(
            cooperative_id=cooperative_id,
            date__year=month.year,
            date__month=month.month
        )
        total_expenses = expenses.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        event_count = DeviceEvent.objects.filter(
            device_id__in=devices,
            timestamp__range=[start_date, end_date],
            processed=True,
            event_type=0,
        ).exclude(Q(payed="sub"))

        event_sum_count = event_count.aggregate(event_sum=Sum('payed'))['event_sum'] or 0

        subscriptions = Subscription.objects.filter(
            cooperative_id=cooperative_id,
            start_date__range=[start_date, end_date]
        )
        sum_subscription_price = subscriptions.aggregate(total_price=Sum('price'))['total_price'] or 0

        total_amount = int(event_sum_count) + sum_subscription_price
        net_total = total_amount - total_expenses
        
        # Format the month name to Georgian
        month_name_georgian = georgian_month_names[month.strftime('%B')]
        
        tab_data.append({
            'month': f"{month_name_georgian} {month.year}",
            'expenses': expenses,
            'total_expenses': total_expenses,
            'total_amount': total_amount,
            'net_total': net_total
        })
    
    return render(request, 'cooperative.html', {'last_six_months': last_six_months, 
                                                'tab_data': tab_data,
                                                'cooperative_balance': cooperative_balance})




@login_required
def generate_qr(request):
    if request.method == 'POST':
        # Get form data
        for_mobile = request.POST.get('for_mobile')
        life_hours = request.POST.get('life_hours')

        # Check if the user already has 2 cards
        if request.user.cards.count() >= 3:
            message = "qr-ების ლიმიტი ამოგეწურა"
            return render(request, 'guest.html', 
                {'message': message})

        # Generate a random 10-digit number
        random_number = ''.join(random.choices(string.digits, k=10))
        
        if Card.objects.filter(card_number=random_number).exists():
            # If a card with this number already exists, generate a new random number
            random_number = ''.join(random.choices(string.digits, k=10))
            
        # Create a new card associated with the current user
        Card.objects.create(card_number=random_number, user=request.user, temp=True, for_mobile=for_mobile, life_hours=life_hours)
        SubsObserverLog.objects.create(card_number=random_number, operation_to_do="add card", processed=False, user_id=request.user.id)

        # Generate QR code with the card number
        qr = qrcode.make(random_number)

        # Save QR code image
        image_name = f'qr_{random_number}.png'
        with default_storage.open(image_name, 'wb') as f:
            qr.save(f, 'PNG')

        # Send SMS with the QR code link
        qr_link = request.build_absolute_uri(default_storage.url(image_name))
        sms_content = f"Here is your QR code link: {qr_link}"
        send_sms(for_mobile, sms_content)
        message = "სტუმარს გაეგზავნა qr კოდი"
        return render(request, 'guest.html', 
                      {'message': message})
    else:
        # Handle GET request if needed
        return HttpResponse("GET method not allowed for this view.", status=405)


@login_required
def card_usage(request):
    # Get the current user
    current_user_id = request.user.id

    # Get all device events associated with the current user's cards
    user_device_events = DeviceEvent.objects.filter(user=current_user_id, processed=1).order_by('-timestamp')

    # Paginate the queryset to display 5 records per page
    paginator = Paginator(user_device_events, 10)
    page_number = request.GET.get('page')

    try:
        user_device_events_paginated = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        user_device_events_paginated = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        user_device_events_paginated = paginator.page(paginator.num_pages)

    # Pass the paginated device events to the template context
    return render(request, 'card_usage.html', {'user_device_events': user_device_events_paginated})

@login_required
def finances(request):
    user_balance = Balance.objects.get(user=request.user).user_balance
    if request.method == 'POST':
        subscription_type_id = request.POST.get('subscription_type_id')
        subscription_type = SubscriptionType.objects.get(pk=subscription_type_id)
        cooperative_id = request.user.cooperative_id
        # Check if the user already has an active subscription
        if Subscription.objects.filter(user=request.user, is_active=True).exists():
            message = "შენ უკვე გაქვს აქტიური აბონემენტი."
        else:
            # Retrieve the Cooperative instance using the cooperative_id
            cooperative_instance = Cooperative.objects.get(pk=cooperative_id)
            # Calculate end date for the subscription
            start_date = datetime.now()
            end_date = start_date + timedelta(days=subscription_type.subscription_days)

            # Check if the user has enough balance for the subscription
            if request.user.balance.user_balance >= subscription_type.subscription_price:
                # Use atomic transaction to ensure data consistency
                with transaction.atomic():
                    # Deduct subscription price from user balance
                    request.user.balance.user_balance = F('user_balance') - subscription_type.subscription_price
                    request.user.balance.save()

                    # Create a new subscription with the correct Cooperative instance
                    Subscription.objects.create(
                        user=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        cooperative=cooperative_instance, 
                        price=subscription_type.subscription_price
                    )
                    # Send SMS to the user about the subscription
                    destination = request.user.mobile_number
                    content = "Your subscription has been created successfully"  # Modify message as needed
                    send_sms(destination, content)
                message = "აბონემენტი წარმატებით დაემატა."
            else:
                message = "ბალანსი არასაკმარისია."
        
        # Fetch the user's existing subscriptions
        user_subscriptions = Subscription.objects.filter(user=request.user).order_by('-start_date')
        subscription_status = False
        subscription_end_date = ''
        for subscription in user_subscriptions:
            if(subscription.is_active == True):
                subscription_status = True
                subscription_end_date = subscription.end_date
            else: 
                pass
        # Retrieve all completed transactions associated with the current user
        user_transactions = Transaction.objects.filter(user=request.user, status='complete').order_by('-created_at')
        subscription_types = SubscriptionType.objects.filter(cooperative_id=request.user.cooperative_id)
        updated_balance = Balance.objects.get(user=request.user).user_balance
        return render(request, 'finances.html', 
                      {'subscription_types': subscription_types, 
                       'user_subscriptions': user_subscriptions, 
                       'message': message, 'user_balance': updated_balance, 
                       'subscription_status': subscription_status, 
                       'subscription_end_date': subscription_end_date, 
                       'user_transactions': user_transactions})

    # Fetch the user's existing subscriptions
    user_subscriptions = Subscription.objects.filter(user=request.user).order_by('-start_date')

    subscription_status = False
    subscription_end_date = ''
    for subscription in user_subscriptions:
        if(subscription.is_active == True):
            subscription_status = True
            subscription_end_date = subscription.end_date
        else: 
            pass

    # Retrieve all completed transactions associated with the current user
    user_transactions = Transaction.objects.filter(user=request.user, status='complete').order_by('-created_at')
    subscription_types = SubscriptionType.objects.filter(cooperative_id=request.user.cooperative_id)

    return render(request, 'finances.html', 
                  {'subscription_types': subscription_types, 
                   'user_subscriptions': user_subscriptions, 
                   'user_balance': user_balance, 
                   'subscription_status': subscription_status, 
                   'subscription_end_date': subscription_end_date, 
                   'user_transactions': user_transactions})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.password_changed = True
            request.user.save()
            return redirect('dashboard')
    else:
        form = PasswordChangeForm()
    return render(request, 'change_password.html', {'form': form})



def send_recovery_sms(request):
    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number')
        if Client.objects.filter(mobile_number=mobile_number).exists():
            verification_code = get_random_string(length=4, allowed_chars='0123456789')
            send_sms(mobile_number, verification_code)
            print("Verification code:", verification_code)

            request.session['verification_code'] = verification_code
            request.session['mobile_number'] = mobile_number
            return redirect('verify_code')  # Redirect to the verify_code view
        else:
            messages.error(request, "ტელეფონის ნომერი არ მოიძებნა")
    return render(request, 'send_sms.html')

def verify_code(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        stored_code = request.session.get('verification_code')
        if entered_code == stored_code:
            mobile_number = request.session.get('mobile_number')
            if Client.objects.filter(mobile_number=mobile_number).exists():
                request.session['code_verified'] = True
                request.session.save()
                return redirect('update_password')  # Redirect to update_password view
            else:
                messages.error(request, "ტელეფონის ნომერი არ მოიძებნა")
        else:
            messages.error(request, "კოდი არასწორია")
    return render(request, 'verify_sms.html')

def update_password(request):
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, "პაროლები ერთმანეთს არ ემთხვევა")
        else:
            mobile_number = request.session.get('mobile_number')
            client = Client.objects.get(mobile_number=mobile_number)
            client.password = make_password(password1)
            client.password_changed = True
            client.save()

            user = authenticate(username=client.username, password=password1)
            if user is not None:
                login(request, user)
                update_session_auth_hash(request, user)

            return redirect('dashboard')
    return render(request, 'update_password.html')