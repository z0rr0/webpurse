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
from webpurse.settings import BANK_FILE

import datetime

LAST_PAYS = 10

# INDEX PAGE *************************
@login_required
def home(request, vtemplate):
    # data from cookie
    form_def = {}
    for prefix in ('in_', 'out_'):
        form_def[prefix] = {}
        invoice_pref = prefix + 'invoice'
        itype_pref = prefix + 'itype'
        if invoice_pref in request.COOKIES:
            form_def[prefix]['invoice'] = request.COOKIES[invoice_pref]
        if itype_pref in request.COOKIES:
            form_def[prefix]['itype'] = request.COOKIES[itype_pref]
    # create forms
    form_in, form_out = get_pay_forms(request.user, form_def)
    response = HttpResponse()
    rest = direct_to_template(request, vtemplate, {
        'form_in': form_in, 
        'form_out': form_out})
    return rest

def get_pay_forms(vuser, form_def):
    user_itype = Itype.aobjects.filter(user=vuser)
    user_invoice = Invoice.objects.filter(user=vuser)
    form_in = PayForm(initial=form_def['in_'], auto_id='in_%s')
    form_out = PayForm(initial=form_def['out_'], auto_id='out_%s')
    # invoice
    invoice_choices = [(s.id, s.name) for s in user_invoice]
    form_in.fields['invoice'].choices = invoice_choices
    form_out.fields['invoice'].choices = invoice_choices
    # itype
    form_in.fields['itype'].choices = [(s.id, s.name) for s in user_itype.filter(sign=False)]
    form_out.fields['itype'].choices = [(s.id, s.name) for s in user_itype.filter(sign=True)]
    return form_in, form_out

 # INVOICE *************************
def user_invoices(user_id):
    invoices = Invoice.objects.select_related().filter(user=user_id)
    summ_inv = invoices.filter(other=False)
    summ = 0
    for s in summ_inv:
        summ += s.balance * s.valuta.kurs
    # summ = summ.aggregate(Sum('balance'))
    return invoices, summ

# VIEW INVOICES LIST AND ALL SUM BALANCE
@login_required
def invoice_view(request, vtemplate):
    invoices, summ = user_invoices(request.user.id)
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ
        });

# TABLE USERS INVOICES
@login_required
def invoice_all(request, vtemplate):
    invoices, summ = user_invoices(request.user.id)
    # edit spec form
    c = {}
    c.update(csrf(request))
    form = InvoiceForm()
    form.fields['valuta'].choices = [(s.id, 
        ("%s: %s" % (s.code, s.name))) for s in Valuta.objects.all()]
    # form.fields['name'].widget = forms.TextInput(attrs={'size':'20'})
    # form.fields['balance'].widget = forms.TextInput(attrs={'size':'20'})
    # form.fields['url'].widget = forms.TextInput(attrs={'size':'50'})
    # form.fields['comment'].widget = forms.forms.Textarea(attrs={'cols': '60', 'rows': '2'})
    # return response request
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ, 'form': form
        });

# AUTH USER
def invoice_perm(user):
    return user.is_authenticated() and user.has_perm("invoice.can_delete")

# DELETE SELEST INVOICE 
# delete invoice, additional var: login_url="/accounts/login/"
# or @user_passes_test(invoice_perm)
@permission_required('purse.delete_invoice')
@transaction.autocommit
def invoice_delete(request, id, redirecturl):
    invoice = get_object_or_404(Invoice, pk=int(id), user=request.user.id)
    if invoice:
         invoice.delete()
    return HttpResponseRedirect(redirecturl)

# DELETE SELECT INVOICE
@permission_required('purse.delete_itype')
@transaction.autocommit
def invoice_delete(request, id, redirecturl):
    qstatus = 'faile'
    itype = get_object_or_404(Itype, pk=int(id), user=request.user.id)
    if itype:
         itype.delete()
         qstatus = 'ok'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# EDIT SELECT INVOICE'S OR ADD <= 5 ROWS
@permission_required('purse.change_invoice')
def invoice_edit(request, vtemplate):
    c = {}
    c.update(csrf(request))
    qinvoice = Invoice.objects.filter(user=request.user.id)
    if qinvoice.count():
        extra_num = 0
    else:
        extra_num = 5     
        qinvoice = Invoice.objects.none()
    # formset
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
    return direct_to_template(request, vtemplate, {'formset': formset})

# ADD NEW USER INVOICE
@permission_required('purse.add_invoice')
@transaction.autocommit
def invoice_add(request, vtemplate):
    c = {}
    c.update(csrf(request))
    valutas = Valuta.objects.all()
    if request.method == 'POST':
        form = InvoiceForm(request.POST or None) 
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.user_id = request.user.id
            invoice.save()
            return redirect('/invoices/')
    else:
        form = InvoiceForm()      
    form.fields['valuta'].choices = [(s.id, ("%s: %s" % (s.code, s.name))) for s in valutas]
    return direct_to_template(request, vtemplate, {'form': form})

# ADD NEW PAY (+ OR -)
@permission_required('purse.add_pay')
def pay_add(request, vtemplate):
    save_cookie = False
    if request.method == 'POST':
        try:
            value = float(request.POST['value'])
            itype = get_object_or_404(Itype, pk=int(request.POST['itype']))
            invoice = get_object_or_404(Invoice, pk=int(request.POST['invoice']))
            value = -abs(value) if itype.sign else abs(value)
            new_balance = invoice.balance + value
            with transaction.commit_on_success():
                pay = Pay.objects.create(invoice=invoice,
                    itype=itype,   
                    pdate=datetime.datetime.strptime(request.POST['pdate'], "%d.%m.%Y").date(),
                    value=value,
                    comment=request.POST['comment']
                )
                Invoice.objects.filter(id=pay.invoice_id).update(balance=new_balance)
            # save cookie vars
        except:
            raise Http404
            qstatus = 'faile'
        qstatus = 'ok'
        save_cookie = True
    else:
        qstatus = 'faile'
    rest = direct_to_template(request, vtemplate, {'qstatus': qstatus})
    if save_cookie:
        prefix = 'in_' if value > 0 else 'out_'
        # OR rest.delete_cookie(prefix + 'invoice')
        rest.set_cookie(prefix + 'invoice', pay.invoice_id)
        rest.set_cookie(prefix + 'itype', pay.itype_id)
    return rest

# EDIT PAY
@permission_required('purse.change_pay')
def pay_edit(request, id, vtemplate):
    c = {}
    c.update(csrf(request))
    user_itypes = Itype.aobjects.filter(user=request.user)
    user_invoices = Invoice.objects.filter(user=request.user)
    # get pay by id
    pay = get_object_or_404(Pay, id=int(id), invoice__user=request.user)
    if request.method == 'POST':
        form = PayEditForm(request.POST or None) 
        if form.is_valid():
            pay = form.save(commit=False)
            # invoice.save()
            # return redirect('/invoices/')
    else:
        pay.value = abs(pay.value)
        form = PayEditForm(instance=pay)
    form.fields['invoice'].choices = [(s.id, s.name) for s in user_invoices]
    # itype items
    items=[(u"Доход", [(s.id, s.name) for s in user_itypes.filter(sign=False)]),
        (u"Расход", [(s.id, s.name) for s in user_itypes.filter(sign=True)])]
    form.fields['itype'].choices = items
    return direct_to_template(request, vtemplate, {
        'form': form,
        })

# VIEW LAST PAY'S
@login_required
def pay_last(request, vtemplate):
    # day_border = datetime.datetime.now().date() - datetime.timedelta(days=LAST_PAYS)
    invoices = Invoice.objects.filter(user=request.user).only('id')
    # pays = Pay.objects.filter(invoice__in=[ val.id for val in invoices ]).order_by('-pdate')[:LAST_PAYS]
    pays = Pay.objects.filter(invoice__user=request.user).order_by('-pdate')[:LAST_PAYS]
    return direct_to_template(request, vtemplate, {'pays': pays, })

# ALL USER ITYPE'S
@login_required
def itypes_all(request, vtemplate):
    user_itype = Itype.aobjects.filter(user=request.user)
    itype_in = user_itype.filter(sign=False)
    itype_out = user_itype.filter(sign=True)
    return direct_to_template(request, vtemplate, {
        'itype_in': itype_in,
        'itype_out': itype_out
        })

# USER ITYPE FILTERS BY SIGN
@login_required
def itype_view(request, sign, vtemplate):
    itypes = Itype.aobjects.filter(user=request.user, sign=sign)
    sign = int(sign)
    return direct_to_template(request, vtemplate, {
        'itypes': itypes,
        'sign': sign
        })

# ADD ITYPE WITH SELECTED SIGN - OR - EDIT ITYPE NAME
@permission_required('purse.add_itype')
@transaction.autocommit
def itype_add(request, vtemplate):
    if request.method == 'POST':
        try:
            if 'id' in request.POST:
                # update        
                id = int(request.POST['id'])
                itype = Itype.objects.filter(id=id, user=request.user)
                itype.update(name=request.POST['name'])
            else:
                # create
                sign = int(request.POST['sign'])
                sign = bool(sign)        
                itype = Itype.objects.create(name=request.POST['name'],
                    user=request.user,
                    sign=sign,
                )
        except:
            raise Http404
            qstatus = 'faile'
        qstatus = 'ok'
    else:
        qstatus = 'faile'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# DELETE ITYPE (STATUS=FALSE)
@permission_required('purse.chage_itype')
@transaction.autocommit
def itype_del(request, id, vtemplate):
    itype = Itype.objects.filter(id=int(id), user=request.user)
    if itype:
        itype.update(status=False)
        qstatus = 'ok'
    else:
        qstatus ='faile'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# VIEW ITYPE FOR EDIT FORM
@permission_required('purse.chage_itype')
@transaction.autocommit
def itype_edit(request, id, vtemplate):
    try:
        itype = Itype.objects.get(id=int(id), user=request.user)
        sign = int(itype.sign)
    except Itype.DoesNotExist, ValueError:
        raise Http404
    return direct_to_template(request, vtemplate, {'itype': itype, 'sign': sign})
