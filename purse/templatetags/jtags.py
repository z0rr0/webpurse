#-*- coding: utf-8 -*-
from django import template
import locale

locale.setlocale(locale.LC_ALL, "")
register = template.Library()

@register.filter(name='income')
def income(value):
    return 'расход' if value else 'доход'

@register.filter(name='rusnum')
def rusnum(value):
    return locale.format('%0.2f', value, True)

@register.filter(name='myinvoice')
def rusnum(value):
    return '-' if value else '+'
