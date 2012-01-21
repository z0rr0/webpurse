#-*- coding: utf-8 -*-
from django.contrib import admin
from main.purse import models

admin.site.register(models.Invoice)
admin.site.register(models.Itype)
admin.site.register(models.Pay)
admin.site.register(models.Futpay)
admin.site.register(models.Dept)
admin.site.register(models.Transfer)
admin.site.register(models.Valuta)
