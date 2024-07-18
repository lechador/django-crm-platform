from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, Card, Cooperative, SubscriptionType, Balance, CooperativeExpense, SmsText
from .forms import ClientForm

class ClientAdmin(UserAdmin):
    form = ClientForm
    list_display = ('id','username', 'first_name', 'last_name', 'mobile_number', 'is_staff', "apartment_number", "cooperative_id")
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('პირადი ინფორმაცია', {'fields': ('first_name', 'last_name','mobile_number', 'apartment_number', 'cooperative_id', 'allowed_cooperatives')}),
        ('უფლებები', {'fields': ('is_active', 'is_staff', 'is_superuser', 'head')}),
        ('თარიღები', {'fields': ('last_login',)}),
    )
    search_fields = ('username', 'first_name', 'last_name' 'mobile_number')
    ordering = ('username',)



class CardAdmin(admin.ModelAdmin): 
    list_display = ("card_number", "user_id")

class CoopExpense(admin.ModelAdmin): 
    list_display = ("cooperative_id", "amount", "date", "description")

class BalanceAdmin(admin.ModelAdmin): 
    list_display = ("user_balance", "user_id")
    fieldsets = (
        (None, {'fields': ('user_balance',)}),
    )

class SmsAdmin(admin.ModelAdmin): 
    list_display = ("case", "text")

class CooperativeAdmin(admin.ModelAdmin): 
    list_display = ("id", "cooperative_name", "cooperative_address", "cooperative_device_price")

class SubscriptionTypeAdmin(admin.ModelAdmin): 
    list_display = ("id", "subscription_name", "subscription_days", "subscription_price", "cooperative_id")

admin.site.register(Client, ClientAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Cooperative, CooperativeAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Balance, BalanceAdmin)
admin.site.register(CooperativeExpense, CoopExpense)
admin.site.register(SmsText, SmsAdmin)