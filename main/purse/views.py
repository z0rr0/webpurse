#-*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.response import TemplateResponse
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
# from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template
from django.forms.models import modelformset_factory
# from django.forms import Textarea
from django.contrib import auth
from django.utils import simplejson
from django.forms.extras import widgets
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db import transaction
from django.db.models import Q, F, Sum
from django import forms
# new
# from django.template.response import TemplateResponse
# import the logging library
# import logging
# Get an instance of a logger
# logger = logging.getLogger(__name__)

from main.purse.models import *
from main.purse.forms import *
from main.settings import BANK_FILE

from dateutil.relativedelta import relativedelta
from googlecharts import time_series
from qsstats import QuerySetStats
from operator import attrgetter
import datetime
import logging

LAST_PAYS = 15
CORRECT_PAY_NAME = u'Корректировка'
logger = logging.getLogger(__name__)

# INDEX PAGE *************************
@login_required
def home(request, vtemplate):
    u"""
    Base page :model:`purse.Invoice`, :model:`purse.Valuta`

    **Context**

    ``RequestContext``

    ``mymodel``
        An instance of :model:`purse.Invoice`. :model:`purse.Valuta`

    **Template:**

    :template:`purse/home.html`

    """
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
    form_in, form_out, form_cor, form_trans, form_dept = get_pay_forms(request.user, form_def)
    return direct_to_template(request, vtemplate, {
            'form_in': form_in, 
            'form_out': form_out,
            'form_cor': form_cor,
            'form_trans': form_trans,
            'form_dept': form_dept
            })

def get_pay_forms(vuser, form_def):
    user_itype = Itype.aobjects.filter(user=vuser, correction=False)
    user_invoice = Invoice.objects.filter(user=vuser)
    form_in = PayForm(initial=form_def['in_'], auto_id='in_%s')
    form_out = PayForm(initial=form_def['out_'], auto_id='out_%s')
    form_cor = PayCorrectForm(auto_id='cor_%s')
    form_trans = TransferForm(auto_id='trans_%s')
    form_dept = DeptForm(auto_id='dept_%s')
    # invoice
    invoice_choices = [(s.id, s.name) for s in user_invoice]
    form_in.fields['invoice'].choices = invoice_choices
    form_out.fields['invoice'].choices = invoice_choices
    form_cor.fields['invoice'].choices = invoice_choices
    form_dept.fields['invoice'].choices = invoice_choices
    # trans
    jsevent = "update_trans('ito','ifrom', 0)"
    form_trans.fields['ifrom'].widget = forms.Select(attrs={
        'id': 'trans_ifrom',
        'onchange': jsevent})
    form_trans.fields['ifrom'].choices = invoice_choices
    # itype
    form_in.fields['itype'].choices = [(s.id, s.name) for s in user_itype.filter(sign=False)]
    form_out.fields['itype'].choices = [(s.id, s.name) for s in user_itype.filter(sign=True)]
    return form_in, form_out, form_cor, form_trans, form_dept

 # INVOICE *************************
def sum_user_invoices(user_id):
    invoices = Invoice.objects.select_related().filter(user=user_id)
    summ_inv = invoices.filter(other=False)
    summ_invother = invoices.filter(other=True)
    summ, summ_other = 0, 0
    for s in summ_inv:
        summ += s.balance * s.valuta.kurs
    for s in summ_invother:
        summ_other += s.balance * s.valuta.kurs
    # summ = summ.aggregate(Sum('balance'))
    # search depts
    depts = Dept.objects.filter(invoice__user=user_id).order_by('taker').values('taker', 'invoice__valuta__code')
    dgt = depts.annotate(sdept=Sum('value')).filter(sdept__gt=0)
    dlt = depts.annotate(sdept=Sum('value')).filter(sdept__lt=0)
    depts = {'dgt': dgt, 'dlt': dlt}
    return invoices, summ, summ_other, depts

# VIEW INVOICES LIST AND ALL SUM BALANCE
@login_required
def invoice_view(request, vtemplate):
    invoices, summ, summ_other, depts = sum_user_invoices(request.user.id)
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ, 'summ_other': summ_other, 'depts': depts
    });

# TABLE USERS INVOICES
@login_required
def invoice_all(request, vtemplate):
    invoices, summ, summ_other, depts = sum_user_invoices(request.user.id)
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
        'invoices': invoices, 'form': form, 
        'summ': summ, 'summ_other': summ_other,
        'summ_all': summ + summ_other
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
            itype = get_object_or_404(Itype, pk=int(request.POST['itype']), user=request.user)
            invoice = get_object_or_404(Invoice, pk=int(request.POST['invoice']), user=request.user)
            value = -abs(value) if itype.sign else abs(value)
            with transaction.commit_on_success():
                pay = Pay.objects.create(invoice=invoice,
                    itype=itype,   
                    pdate=datetime.datetime.strptime(request.POST['pdate'], "%d.%m.%Y").date(),
                    value=value,
                    comment=request.POST['comment']
                )
                # update invoice
                pay.invoice.balance = F('balance') + pay.value
                pay.invoice.save()
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
        # save cookie vars
        rest.set_cookie(prefix + 'invoice', pay.invoice_id)
        rest.set_cookie(prefix + 'itype', pay.itype_id)
    return rest

# ADD NEW CORRECT PAY
@permission_required('purse.add_pay')
def pay_correct(request, vtemplate):
    save_cookie = False
    if request.method == 'POST':
        with transaction.commit_on_success():
            invoice = get_object_or_404(Invoice, 
                pk=int(request.POST['invoice']), user=request.user)
            try:
                tosum = int(request.POST['tosum'])
                if tosum:
                    value = float(request.POST['value']) - invoice.balance
                else:
                    value = float(request.POST['value'])
                # create or search cor itype
                itype, created = Itype.objects.get_or_create(correction=True, 
                    user=request.user, name=CORRECT_PAY_NAME) 
                # save new pay
                pay = Pay.objects.create(invoice=invoice,
                    itype=itype,   
                    pdate=datetime.datetime.strptime(request.POST['pdate'], "%d.%m.%Y").date(),
                    value=value,
                    comment=request.POST['comment'])
                # update invoice
                invoice.balance = F('balance') + value
                invoice.save()
            except:
                raise Http404
                qstatus = 'faile'
            qstatus = 'ok'
    else:
        qstatus = 'faile'
    qstatus = bool(int(request.POST['tosum']))
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

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
        old_invoice, old_value = pay.invoice, pay.value
        form = PayEditForm(request.POST or None, instance=pay) 
        if form.is_valid():
            with transaction.commit_on_success():
                # del pay value in old invoice
                old_invoice.balance = F('balance') - old_value
                old_invoice.save()
                # new pay
                new_pay = form.save(commit=False)
                if not new_pay.itype.correction:
                    new_pay.value = -abs(pay.value) if pay.itype.sign else abs(pay.value)
                new_pay.save()
                # edit balance new invoice
                new_pay.invoice.balance = F('balance') + new_pay.value
                new_pay.invoice.save()
                return redirect('/')
    else:
        if not pay.itype.correction:
            pay.value = abs(pay.value)
        form = PayEditForm(instance=pay)
    form.fields['invoice'].choices = [(s.id, s.name) for s in user_invoices]
    # itype items
    items=[(u"Доход", [(s.id, s.name) for s in user_itypes.filter(sign=False)]),
        (u"Расход", [(s.id, s.name) for s in user_itypes.filter(sign=True)])]
    form.fields['itype'].choices = items
    return direct_to_template(request, vtemplate, { 'form': form })

# DELETE PAY
@permission_required('purse.delete_pay')
def pay_del(request, id, vtemplate):
    pay = get_object_or_404(Pay, id=int(id), invoice__user=request.user)
    with transaction.commit_on_success():
        # update blance
        Invoice.objects.filter(id=pay.invoice_id).update(balance=F('balance') - pay.value)
        # delete
        pay.delete()
    qstatus = 'ok'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# VIEW LAST PAY'S
@login_required
def pay_last(request, vtemplate):
    pays = Pay.objects.filter(invoice__user=request.user).order_by('-pdate', '-modified')[:LAST_PAYS]
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
@permission_required('purse.change_itype')
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
@permission_required('purse.change_itype')
@transaction.autocommit
def itype_edit(request, id, vtemplate):
    try:
        itype = Itype.objects.get(id=int(id), user=request.user)
        sign = int(itype.sign)
    except Itype.DoesNotExist, ValueError:
        raise Http404
    return direct_to_template(request, vtemplate, {'itype': itype, 'sign': sign})

# WORK WITH TRANSFER PAY'S, CREATE SELECT
@login_required
def transfer_update(request, vtemplate):
    form = TransSmallForm()
    if request.method == 'POST':
        try:
            if request.POST['val']:
                form = TransSmallForm(initial={'ito': int(request.POST['defaulid'])})
                # jsevent = "update_trans('" + request.POST['eventid'] + "','" + request.POST['form_id'] + "')"
                form.fields['ito'].widget = forms.Select(attrs={
                    'id': 'trans_' + request.POST['form_id'],
                    # 'onchange': jsevent
                    })
                # invoice
                user_invoice = Invoice.objects.filter(user=request.user).exclude(id=int(request.POST['val']))
                invoice_choices = [(s.id, s.name) for s in user_invoice]
                form.fields['ito'].choices = invoice_choices
        except:
            raise Http404
    return direct_to_template(request, vtemplate, {'form': form})

# ADD PAY TRANSFER
@permission_required('purse.add_transfer')
def transfer_add(request, vtemplate):
    if request.method == 'POST':
        try:
            with transaction.commit_on_success():
                value = abs(float(request.POST['value']))
                # invoices
                ifrom = Invoice.objects.get(pk=int(request.POST['ifrom']), user=request.user)
                ito = Invoice.objects.get(pk=int(request.POST['ito']), user=request.user)
                # change
                ifrom.balance = F('balance') - value
                value_by_kurs = round(ifrom.valuta.kurs * value / ito.valuta.kurs, 2)
                ito.balance = F('balance') + value_by_kurs
                # save
                ifrom.save()
                ito.save()
                # transfer
                transfer = Transfer.objects.create(ifrom=ifrom, ito=ito, 
                    pdate=datetime.datetime.strptime(request.POST['pdate'], "%d.%m.%Y").date(), 
                    comment=request.POST['comment'],
                    value=value)
        except:
            raise Http404
            qstatus = 'faile'
        qstatus = 'ok'
    else:
        qstatus = 'faile'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# LAST TRANSFER'S
@login_required
def transfer_last(request, vtemplate):
    transfers = Transfer.objects.filter(Q(ifrom__user=request.user) | Q(ito__user=request.user))
    transfers = transfers.order_by('-pdate', '-modified')[:LAST_PAYS]
    return direct_to_template(request, vtemplate, {'transfers': transfers})

# DELETE TRANSFER
@permission_required('purse.delete_transfer')
def transfer_del(request, id, vtemplate):
    transfer = get_object_or_404(Transfer, id=int(id), ifrom__user=request.user)
    try:
        with transaction.commit_on_success():
            # change
            transfer.ifrom.balance = F('balance') + transfer.value
            value_by_kurs = round(transfer.ifrom.valuta.kurs * transfer.value / transfer.ito.valuta.kurs, 2)
            transfer.ito.balance = F('balance') - value_by_kurs
            # save
            transfer.ifrom.save()
            transfer.ito.save()
            # delete
            transfer.delete()
    except:
        raise Http404
        qstatus = 'faile'
    qstatus = 'ok'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# EDIT TRANSFER
@permission_required('purse.change_pay')
def transfer_edit(request, id, vtemplate):
    c = {}
    c.update(csrf(request))
    ititito = 0
    transfer = get_object_or_404(Transfer, id=int(id), ifrom__user=request.user)
    old_value = transfer.value
    # invoices
    ifrom, ito = transfer.ifrom, transfer.ito
    # init form
    form = TransferEditForm(auto_id='trans_%s', instance=transfer)
    if request.method == 'POST':
        form = TransferEditForm(request.POST or None, auto_id='trans_%s', instance=transfer)
        if form.is_valid():
            with transaction.commit_on_success():
                try:
                    new_trans = form.save(commit=False)
                    new_trans.value = abs(float(new_trans.value))
                    new_trans.save()
                    # del old trans invoice
                    ifrom.balance = F('balance') + old_value
                    value_by_kurs = round(ifrom.valuta.kurs * old_value / ito.valuta.kurs, 2)
                    ito.balance = F('balance') - value_by_kurs
                    # save
                    ifrom.save()
                    ito.save()
                    # ************************
                    # create new trans invoice
                    ifrom, ito = new_trans.ifrom, new_trans.ito
                    new_trans.ifrom.balance = F('balance') - new_trans.value
                    value_by_kurs = round(new_trans.ifrom.valuta.kurs * new_trans.value / new_trans.ito.valuta.kurs, 2)
                    new_trans.ito.balance = F('balance') + value_by_kurs
                    # save
                    new_trans.ifrom.save()
                    new_trans.ito.save()
                    initito = new_trans.ito_id
                    return redirect('/')
                except:
                    raise Http404
        else:
            initito = request.POST['ito']
    else:
        initito = transfer.ito_id
     # trans select
    jsevent = "update_trans('ito','ifrom', " + str(initito) + ")"
    form.fields['ifrom'].widget = forms.Select(attrs={
        'id': 'trans_ifrom',
        'onchange': jsevent})
    form.fields['ifrom'].choices = [(s.id, s.name) for s in Invoice.objects.filter(user=request.user)]
    return direct_to_template(request, vtemplate, { 'form': form, 'initito': initito })

# DEPTS AUTOCOMLETE
@login_required
def dept_complete(request):
    result = []
    if request.method == 'POST':
        try:
            depts = Dept.objects.filter(invoice__user=request.user, 
                taker__istartswith=request.POST['val']).order_by('taker')
            depts = depts.values('taker').distinct()
            result = [ x['taker'] for x in depts ]
        except IndexError:
            pass
    return HttpResponse(simplejson.dumps(result), mimetype='application/json')

# LAST DEPTS
@login_required
def depts_last(request, vtemplate):
    depts = Dept.objects.filter(invoice__user=request.user)
    depts = depts.order_by('-pdate', '-modified')[:LAST_PAYS]
    return direct_to_template(request, vtemplate, {'depts': depts})

# ADD DEPT
@permission_required('purse.add_dept')
def dept_add(request, vtemplate):
    if request.method == 'POST':
        try:
            with transaction.commit_on_success():
                value = abs(float(request.POST['value']))
                credit = int(request.POST['credit'])
                value = value if credit else -value
                # invoices
                invoice = Invoice.objects.get(pk=int(request.POST['invoice']), 
                    user=request.user)
                invoice.balance = F('balance') + value
                invoice.save()
                # dept
                dept = Dept.objects.create(invoice=invoice, taker=request.POST['taker'], 
                    pdate=datetime.datetime.strptime(request.POST['pdate'], "%d.%m.%Y").date(), 
                    comment=request.POST['comment'],
                    value=value)
        except:
            raise Http404
            qstatus = 'faile'
        qstatus = 'ok'
    else:
        qstatus = 'faile'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# DELETE DEPT
@permission_required('purse.delete_dept')
def dept_del(request, id, vtemplate):
    dept = get_object_or_404(Dept, id=int(id), invoice__user=request.user)
    try:
        with transaction.commit_on_success():
            # invoices
            dept.invoice.balance = F('balance') - dept.value
            dept.invoice.save()
            # delete
            dept.delete()
    except:
        raise Http404
        qstatus = 'faile'
    qstatus = 'ok'
    return direct_to_template(request, vtemplate, {'qstatus': qstatus})

# EDIT PAY
@permission_required('purse.change_dept')
def dept_edit(request, id, vtemplate):
    c = {}
    c.update(csrf(request))
    user_invoices = Invoice.objects.filter(user=request.user)
    # get pay by id
    dept = get_object_or_404(Dept, id=int(id), invoice__user=request.user)
    if request.method == 'POST':
        old_invoice, old_value = dept.invoice, dept.value
        form = DeptForm(request.POST or None, instance=dept) 
        if form.is_valid():
            with transaction.commit_on_success():
                # del pay value in old invoice
                old_invoice.balance = F('balance') - old_value
                old_invoice.save()
                # new pay
                credit = form.cleaned_data['credit']
                new_dept = form.save(commit=False)
                new_dept.value = abs(dept.value) if credit else -abs(dept.value)
                new_dept.invoice.balance = F('balance') + new_dept.value
                new_dept.save()
                new_dept.invoice.save()
                return redirect('/')
    else:
        if dept.value > 0:
            credit = True
        else:
            dept.value = abs(dept.value)
            credit = False
        form = DeptForm(instance=dept)
        # checked
        if credit:
            form.fields['credit'].widget = forms.CheckboxInput(check_test=True, attrs={'checked': 'checked'})
    form.fields['invoice'].choices = [(s.id, s.name + ' (' + s.valuta.code + ')' ) for s in user_invoices]
    return direct_to_template(request, vtemplate, { 'form': form })

# HISTORY PAGE
@login_required
def history(request, vtemplate):
    date2 = datetime.datetime.now().date()
    date1 = date2 + relativedelta(months=-1)
    # date1 = date2 - datetime.timedelta(days=30)
    return TemplateResponse(request, vtemplate, {'pdate': {'start': date1, 'end': date2}})

# ALL HISTORY VIEW, num 0-2
def search_result_history(user_id, num, d1, d2, comment, ptype=0):
    models = (Pay, Transfer, Dept)
    try:
        if num == 1:
            result = models[num].objects.filter(Q(ifrom__user=user_id) | Q(ito__user=user_id))
        else:
            result = models[num].objects.filter(invoice__user=user_id)
        if ptype:
            if ptype == 1:
                result = result.filter(value__gte=0)
            else:
                result = result.filter(value__lt=0)
    except IndexError:
        return False
    # additional filter
    result = result.filter(pdate__gte=d1, pdate__lte=d2)
    if comment:
        result = result.filter(comment__icontains=comment)
    return parse_result(result.order_by('-pdate', '-modified'), num)

# PARSE SEARCH RESULT
def parse_result(res, num):
    result = []
    for r in res:
        field = {}
        field['id'] = r.id
        field['pdate'] = r.pdate
        field['field2'] = r.value
        field['field5'] = r.comment
        field['field3'] = r.value
        if num == 0:
            field['url'] = 'pay'
            field['field1'] = r.invoice.name
            field['code'] = r.invoice.valuta.code
            field['field4'] = r.itype.name
        elif num == 1:
            field['url'] = 'transfer'
            field['field1'] = r.ifrom.name
            field['code'] = r.ifrom.valuta.code
            field['field4'] = r.ito.name
            field['field3'] = -r.value
        else:
            field['url'] = 'dept'
            field['field1'] = r.invoice.name
            field['code'] = r.invoice.valuta.code
            field['field4'] = r.taker
        result.append(field)
    return result

# HISTORY UPDATE PAGE
@login_required
def history_update(request, vtemplate):
    # status = False
    if request.method == 'POST':
        try:
            date_start = datetime.datetime.strptime(request.POST['date_start'], "%d.%m.%Y").date()
            date_end = datetime.datetime.strptime(request.POST['date_end'], "%d.%m.%Y").date()
            category = int(request.POST['category'])
            paytype = int(request.POST['paytype'])
            result = search_result_history(request.user, category, date_start, date_end, request.POST['comment'], paytype)
        except IndexError:
            pass
    return TemplateResponse(request, vtemplate, { 'result': result })

# USER INTERVAL FOR CALC DIAPAZONE
def user_date_interval(pays, val_time):
    pdate1, pdate2 = pays.order_by('pdate')[0], pays.order_by('-pdate')[0]
    date_func = {'y': date_interval_year, 
        'm': date_interval_month,
        'w': date_interval_week}
    result = date_func[val_time](pdate1.pdate, pdate2.pdate, pays)
    return result
def date_interval_year(start, end, pays):
    result = []
    cur_year = end.year
    while cur_year >= start.year:
        start_year = datetime.date(cur_year, 1, 1)
        result.append([start_year, cur_year])
        cur_year -= 1
    return result
def date_interval_month(start, end, pays):
    year_list = date_interval_year(start, end, pays)
    result = []
    for key, val in year_list:
        pay_years = pays.filter(pdate__year=val)
        current = pay_years.order_by('-pdate')[0].pdate.month
        ml = []
        while current >= pay_years.order_by('pdate')[0].pdate.month:
            start_month = datetime.date(val, current, 1)
            ml.append([start_month, start_month.strftime('%B')])
            current -= 1
        new_row = (val, ml)
        result.append(new_row)
    return result
def search_monday(pdate):
    DAY_IN_WEEK = 7
    return pdate + datetime.timedelta(days=(DAY_IN_WEEK-pdate.weekday()))
def date_interval_week(start, end, pays):
    endw = search_monday(end)
    startw = start + datetime.timedelta(days=-7)
    months = date_interval_month(start, search_monday(end), pays)
    result = []
    for year, month in months:
        for key, name in month:
            ml = []
            # последний день месяца
            current = search_monday(key + relativedelta(months=+1) + datetime.timedelta(days=-1))
            if endw < current:
                current = endw
            while current >= key:
                current2 = current + datetime.timedelta(days=-7)
                if current2 < startw:
                    current = current2
                    continue
                ml.append([current2, "%s - %s" % (current2.strftime('%d.%m'), current.strftime('%d.%m'))])
                current = current2
            val = "%s %s" % (key.strftime('%B'), "'" + str(year - 2000))
            new_row = (val, ml)
            result.append(new_row)
    return result

# REPORT PAGE
@login_required
def report(request, vtemplate):
    c = {}
    c.update(csrf(request))
    user_invoices = Invoice.objects.filter(user=request.user)
    col1, col2 = user_invoices.filter(other=False), user_invoices.filter(other=True)
    user_itype = Itype.aobjects.filter(user=request.user)
    type1, type2 = user_itype.filter(sign=False), user_itype.filter(sign=True)
    values = {'defdiap': 'y'}
    result = {}
    if request.method == 'POST':
        invoices = request.POST.getlist('invoice')
        itypes = request.POST.getlist('itype')
        interval = request.POST['rep_diapazone']
        # default
        definvoices = [x['id'] for x in Invoice.objects.filter(user=request.user, id__in=invoices).values('id')]
        defitypes = [x['id'] for x in Itype.objects.filter(user=request.user, id__in=itypes).values('id')]
        defval = request.POST['diapvalue']
        defdiap = interval
    else:
        defval = Pay.objects.filter(invoice__user=request.user).only('pdate').order_by('-pdate')[0]
        defval = datetime.date(defval.pdate.year,1,1).strftime('%Y-%m-%d')
        definvoices = [x['id'] for x in col1.values('id')]
        defitypes = [x['id'] for x in type1.values('id')] + [x['id'] for x in type2.values('id')]
        defdiap = 'y'
    values['defval'] = defval
    values['defdiap'] = defdiap
    values['defitype'] = defitypes
    values['definvoices'] = definvoices
    # create graph
    start = datetime.datetime.strptime(defval, "%Y-%m-%d").date()
    pdater = pdate_range(start, defdiap)
    if pdater: 
        res = Pay.objects.filter(invoice__user=request.user, itype__user=request.user,
            invoice__in=definvoices, itype__in=defitypes,
            pdate__range=pdater)
        result['graph1'] = get_pdate_graph(pdater, defdiap, res)
        result['graph2'] = get_cat_graph(pdater, defdiap, res, defitypes, False)
        result['graph3'] = get_cat_graph(pdater, defdiap, res, defitypes, True)
        # result['graph2'] = 
        # result['graph2'] = [['foo', 32], ['bar', 64], ['baz', 96]]
    else:
        raise Http404
    # return data
    total_table = {}
    total_table['inv'] = sum([ x[1] for x in result['graph1']])
    total_table['ext'] = sum([ x[2] for x in result['graph1']])
    total_table['plus'] = sum([ x[1] for x in result['graph2']])
    total_table['minus'] = sum([ x[1] for x in result['graph3']])
    return TemplateResponse(request, vtemplate, {'values': values, 'result': result,
        'inv_cols': (col1, col2), 'itype_cols': (type1, type2), 'ttable': total_table})

# CHANGE REPORT DIAPAZONE
@login_required
def report_diapazone(request, vtemplate):
    value = None
    defval = 0
    try:
        if request.method == 'GET':
            val_time = request.GET['val']
            pays = Pay.objects.filter(invoice__user=request.user)
            value = user_date_interval(pays, val_time)
            defval = request.GET['defval']
            # defval = datetime.datetime.now().strftime('%Y-%m-%d')
            # defval = value[-1][-1][-1][0] if val_time in 'mw' else value[-1][0]
            # defval = ''
    except:
        # raise Http404
        pass
    form = ChdiapazoneForm(initial={'diapvalue': defval})
    form.fields['diapvalue'].choices = value
    return direct_to_template(request, vtemplate, {'form': form, 'defval': defval})

def pdate_range(start, interval):
    delta = {'y': relativedelta(years=+1), 
        'm': relativedelta(months=+1),
        'w': relativedelta(days=+7)}
    if interval in 'ymw':
        end = start + delta[interval] + datetime.timedelta(days=-1)
    else:
        return False
    return start, end

def ger_strkey(current, interval):
    if interval == 'y':
        return current.strftime('%b')
    elif interval == 'm':
        border = current + datetime.timedelta(days=+2)
        return "%s-%s" % (current.strftime('%d'), border.strftime('%d'))
    else:
        return current.strftime('%d')
    return None

# CALC RUB VALUTA KURS
def group_valuta_kurs(pay_dict):
    alls = 0
    for s in pay_dict:
        alls += s['invoice__valuta__kurs'] * s['sdept']
    return int(round(alls))

def get_pdate_graph(start_end, interval, pays):
    result = []
    delta = {'y': relativedelta(months=+1), 
        'm': relativedelta(days=+3),
        'w': relativedelta(days=+1)}
    current = start_end[0]
    while current <= start_end[1]:
        strdate = ger_strkey(current, interval)
        d1 = current
        d2 = current + delta[interval]
        psum = pays.filter(pdate__gte=d1, pdate__lt=d2)
        psum = psum.values('invoice__valuta__kurs').annotate(sdept=Sum('value'))
        # result
        result1 = psum.filter(value__gte=0)
        result2 = psum.filter(value__lt=0)
        result1 = group_valuta_kurs(result1)
        result2 = abs(group_valuta_kurs(result2))
        newrow = strdate, result1, result2, result1 - result2
        result.append(newrow)
        current += delta[interval] 
    return result

def get_cat_graph(start_end, interval, pays, itypes, incoming=False):
    result = []
    itypes = Itype.objects.filter(id__in=itypes).only('id', 'name').order_by('name')
    pays = pays.filter(itype__sign=incoming)
    for itype in itypes:
        psum = pays.filter(itype=itype.id)
        psum = psum.values('invoice__valuta__kurs').annotate(sdept=Sum('value'))
        result.append([itype.name, abs(group_valuta_kurs(psum))])
    return sorted(result, key=lambda item: item[1], reverse=True)
