from django import forms
from .models import CooperativeExpense, Cooperative, Client

class PasswordChangeForm(forms.Form):
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")
        
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError("პაროლები არ ემთხვევა")
        
        return cleaned_data

    

class DateRangeForm(forms.Form):
    selected_month = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

class CooperativeExpenseForm(forms.ModelForm):
    class Meta:
        model = CooperativeExpense
        fields = ['date', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ClientForm(forms.ModelForm):
    cooperative_id = forms.ModelChoiceField(queryset=Cooperative.objects.all(), label='Cooperative')

    class Meta:
        model = Client
        fields = '__all__'

    def clean_cooperative_id(self):
        cooperative = self.cleaned_data.get('cooperative_id')
        if cooperative:
            return cooperative.id
        return None

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.cooperative_id = self.cleaned_data['cooperative_id']
        if commit:
            instance.save()
        return instance