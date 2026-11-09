from django import forms
from .models import Tour, Profile, Comment, Departure
class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['title','description','price','categories']
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
class DepartureForm(forms.ModelForm):
    class Meta:
        model = Departure
        fields = ['tour','starts_at']
    def clean_starts_at(self):
        value = self.cleaned_data['starts_at']
        if self.instance.pk and self.instance.bookings.exists() and value != self.instance.starts_at:
            raise forms.ValidationError('Нельзя менять время выезда с бронированиями.')
        return value
