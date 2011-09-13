#-*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
# from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template
from django.forms.models import modelformset_factory
# from django.forms import Textarea
from django.contrib import auth
from django.forms.extras import widgets
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db import transaction
from django.db.models import Sum
from django import forms
# new
# from django.template.response import TemplateResponse
# import the logging library
# import logging
# Get an instance of a logger
# logger = logging.getLogger(__name__)

from webpurse.purse.models import *
from webpurse.purse.forms import *
import datetime


# INDEX PAGE *************************
@login_required
def home(request, vtemplate):
    return direct_to_template(request, vtemplate, {})

 # INVOICE *************************
def user_invoices(user_id):
    invoices = Invoice.objects.filter(user=user_id)
    summ = Invoice.objects.filter(user=user_id, other=False)
    summ = summ.aggregate(Sum('balance'))
    return invoices, summ['balance__sum']

@login_required
def invoice_view(request, vtemplate):
    invoices, summ = user_invoices(request.user.id)
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ
        });

@login_required
def invoice_all(request, vtemplate):
    invoices, summ = user_invoices(request.user.id)
    # edit spec form
    form = InvoiceForm()
    form.fields['name'].widget = forms.TextInput(attrs={'size':'20'})
    form.fields['balance'].widget = forms.TextInput(attrs={'size':'20'})
    form.fields['url'].widget = forms.TextInput(attrs={'size':'50'})
    form.fields['comment'].widget = forms.forms.Textarea(attrs={'cols': '60', 'rows': '2'})
    # return response request
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ, 'form': form
        });

def invoice_perm(user):
    return user.is_authenticated() and user.has_perm("invoice.can_delete")

# delete invoice, additional var: login_url="/accounts/login/"
# or @user_passes_test(invoice_perm)
@permission_required('purse.delete_invoice')
@transaction.autocommit
def invoice_delete(request, id, redirecturl):
    invoice = get_object_or_404(Invoice, pk=int(id), user=request.user.id)
    if invoice:
         invoice.delete()
    return HttpResponseRedirect(redirecturl)

@permission_required('purse.change_invoice')
@transaction.autocommit
def invoice_edit(request, vtemplate):
    c = {}
    c.update(csrf(request))
    qinvoice = Invoice.objects.filter(user=request.user.id)
    if qinvoice.count():
        extra_num = 0
    else:
        extra_num = 5     
        qinvoice = Invoice.objects.none()

    InvoiceFormSet = modelformset_factory(Invoice, extra=extra_num, form=InvoiceForm)
    if request.method == 'POST':
        formset = InvoiceFormSet(request.POST, queryset=qinvoice)
        if formset.is_valid():
            with transaction.commit_on_success():
                for form in formset:
                    # skip empty forms
                    if form.cleaned_data:
                        invoice = form.save(commit=False)
                        invoice.user_id = request.user.id
                        invoice.save()
            return redirect('/invoices/')
    else:
        formset = InvoiceFormSet(queryset=qinvoice)
    return direct_to_template(request, vtemplate, 
        {'formset': formset})
