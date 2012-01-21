#-*- coding: utf-8 -*-
from main.purse import models
from django.forms.extras.widgets import SelectDateWidget
from django import forms

class InvoiceForm(forms.ModelForm):
    # pass

    class Meta:
        model = models.Invoice
        widgets = {'comment': forms.Textarea(attrs={'cols': '30', 'rows': '2'}), 
            'balance': forms.TextInput(attrs={'size': '7'}),
            'url': forms.TextInput(attrs={'size': '22'}),
            'name': forms.TextInput(attrs={'size': '13'})}
        exclude = ('user', 'modified', 'created')
        #fields = ()

class PayForm(forms.ModelForm):
    # pass
    # fields = ("itype", 'itype', 'comment')

    class Meta:
        model = models.Pay
        fields = ('itype', 'invoice', 'value', 'comment')

class PayEditForm(forms.ModelForm):
    # pass
    # fields = ("itype", 'itype', 'comment')

    class Meta:
        model = models.Pay
        fields = ('itype', 'invoice', 'value', 'comment', 'pdate')

class PayCorrectForm(forms.ModelForm):
    # pass
    tosum = forms.BooleanField(label=u'корректировка')

    class Meta:
        model = models.Pay
        fields = ('invoice', 'value', 'comment', 'pdate')

class TransferForm(forms.ModelForm):
    # pass

    class Meta:
        model = models.Transfer
        fields = ('ifrom', 'value', 'comment', 'pdate')

class TransSmallForm(forms.Form):
    ito = forms.ChoiceField(label='', widget=forms.Select(attrs={'id': 'trans_ito'}))

class TransferEditForm(forms.ModelForm):
    # pass

    class Meta:
        model = models.Transfer
        fields = ('ifrom', 'ito', 'value', 'comment', 'pdate')

class DeptForm(forms.ModelForm):
    # pass
    credit = forms.BooleanField(label=u'Получение средств', required=False,
        widget=forms.CheckboxInput(check_test=True))

    class Meta:
        model = models.Dept
        fields = ('invoice', 'taker', 'value', 'comment', 'pdate')

class ChdiapazoneForm(forms.Form):
    diapvalue = forms.ChoiceField(label='', widget=forms.Select(attrs={'id': 'diapvalue'}))