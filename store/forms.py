from django import forms

class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=200)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')], widget=forms.Select)
