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
# from django.forms.extras import widgets
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Sum
# new
# from django.template.response import TemplateResponse
# import the logging library
# import logging
# Get an instance of a logger
# logger = logging.getLogger(__name__)

from webpurse.purse.models import *
# from webpurse.purse.forms import *
import datetime


# INDEX PAGE *************************
@login_required
def home(request, vtemplate):
    return direct_to_template(request, vtemplate, {})

 # INVOICE *************************
@login_required
def invoce_view(request, vtemplate):
    user_id = request.user.id
    invoices = Invoice.objects.filter(user=user_id)
    summ = Invoice.objects.filter(user=user_id, other=False).aggregate(Sum('balance'))
    return direct_to_template(request, vtemplate, {
        'invoices': invoices, 'summ': summ['balance__sum']
        });