from .models import *
from django.forms import ModelForm

# form for leaving comments
class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

    def save(self):
        comment = super(CommentForm, self).save(commit=False)
        comment.save()
        return comment
