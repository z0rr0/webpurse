#-*- coding: utf-8 -*-
from django import template

register = template.Library()

@register.filter(name='income')
def income(value):
    return 'расход' if value else 'доход'
