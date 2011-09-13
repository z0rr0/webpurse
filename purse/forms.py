#-*- coding: utf-8 -*-
from webpurse.purse import models
from django.forms.extras.widgets import SelectDateWidget
from django import forms

class InvoiceForm(forms.ModelForm):
    # pass

    class Meta:
        model = models.Invoice
        # widgets = {'comment': forms.Textarea(attrs={'cols': 30, 'rows': 2}),}
        exclude = ('user', 'modified', 'created')
        #fields = ()