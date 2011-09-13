#-*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
import datetime

# adding methods
def none2str(x):
    return x if x is not None else ''

# CREATE YOUR MODELS HERE.

# ivoices
class Invoice(models.Model):
    user = models.ForeignKey(User, verbose_name=u'пользователь')
    name = models.CharField(max_length=255, verbose_name=u'название')
    balance = models.FloatField(default=0, verbose_name = u'баланс')
    other = models.BooleanField(default=False, verbose_name=u'чужой счет')
    url = models.URLField(max_length=255, verbose_name=u'URL', blank=True, null=True, help_text=u'url')
    comment = models.TextField(verbose_name=u'примечание', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['other', 'name']

# pay types
class Itype(models.Model):
    user = models.ForeignKey(User, verbose_name = u'пользователь')
    sign = models.BooleanField(default=True, verbose_name = u'расход (доход)')
    name = models.CharField(max_length=255, verbose_name=u'название')

    def __unicode__(self):
        itypestr = u'расход' if self.sign else u'доход'
        return '%s (%s)' % (self.name, itypestr)

    class Meta:
        ordering = ['sign', 'name']

# user pays
class Pay(models.Model):
    invoice = models.ForeignKey(Invoice, verbose_name = u'счет')
    itype = models.ForeignKey(Itype, verbose_name = u'тип')
    value = models.FloatField(default=0, verbose_name = u'сумма')
    pdate = models.DateField(verbose_name = u'дата')    
    comment = models.TextField(verbose_name=u'примечание', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return '%s: %s  %s' % (str(self.pdate), self.invoice.name, str(self.value))

    class Meta:
        ordering = ['pdate']

# user futures pays
class Futpay(models.Model):
    PERIOD_CHOICES = (
        ('W', u'неделя'),
        ('M', u'месяц'),
        ('Y', u'год'),
    )
    invoice = models.ForeignKey(Invoice, verbose_name = u'счет')
    itype = models.ForeignKey(Itype, verbose_name = u'тип')
    value = models.FloatField(default=0, verbose_name = u'сумма')
    firstdate = models.DateField(verbose_name = u'дата начала периода', null=True)
    lastdate = models.DateField(verbose_name = u'дата окончания периода', blank=True, null=True)
    period = models.CharField(max_length=1, choices=PERIOD_CHOICES, verbose_name = u'период')
    comment = models.TextField(verbose_name=u'примечание', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return '%s: %s -> %s' % (str(self.pdate), self.Invoice.name, str(self.value))

    class Meta:
        ordering = ['firstdate']

# dept pays
class Dept(models.Model):
    invoice = models.ForeignKey(Invoice, verbose_name = u'счет')
    value = models.FloatField(default=0, verbose_name = u'сумма')
    taker = models.CharField(max_length=255, verbose_name = u'получатель/кредитор')
    pdate = models.DateField(verbose_name = u'дата')    
    comment = models.TextField(verbose_name=u'примечание', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return '%s: %s -> %s (%s)' % (str(self.pdate), 
            self.Invoice.name, str(self.value), self.taker)

    class Meta:
        ordering = ['pdate']

# transfer pays
class Transfer(models.Model):
    ifrom = models.ForeignKey(Invoice, related_name='Ifrom')
    ito = models.ForeignKey(Invoice, related_name='Ito')
    value = models.FloatField(default=0, verbose_name = u'сумма')
    pdate = models.DateField(verbose_name = u'дата')    
    comment = models.TextField(verbose_name=u'примечание', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return '%s: %s -> %s' % (str(self.value), self.ifrom.name, self.ito.name)

    class Meta:
        ordering = ['pdate']
