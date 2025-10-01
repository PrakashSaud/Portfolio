from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message", "consent"]

    def clean_honeypot(self):
        value = self.cleaned_data.get("honeypot")
        if value:
            raise forms.ValidationError("Bot detected.")
        return value

    def clean_consent(self):
        consent = self.cleaned_data.get("consent")
        if not consent:
            raise forms.ValidationError("You must consent to be contacted.")
        return consent
