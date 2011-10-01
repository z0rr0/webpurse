#-*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings

from webpurse.views import ping_test
from webpurse.purse import views as pv

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', pv.home, {
            'vtemplate': 'home.html'}),
    # url(r'^webpurse/', include('webpurse.foo.urls')),
    # server test
    # (r'^ping/$', ping_test),

    # accounts
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$' , logout),
    # left menu
    (r'^invoice/view/$' , pv.invoice_view, {
        'vtemplate': 'invoice_view.html'}),
    # view all user invoices
    (r'^invoices/$' , pv.invoice_all, {
            'vtemplate': 'invoice_all.html'}),
    # del school
    (r'^invoice/delete/(?P<id>\d+)/?$', pv.invoice_delete, {
        'redirecturl': '/invoices/'}),
    # edit all user invoices
    (r'^invoice/edit/$' , pv.invoice_edit, {
        'vtemplate': 'invoice_edit.html'}),
    # add 1 invoice
    (r'^invoice/add/$' , pv.invoice_add, {
        'vtemplate': 'invoice_add.html'}),
    # add pay
    (r'^pay/add/$' , pv.pay_add, {
        'vtemplate': 'pay_add.html'}),
    # edit pay
    (r'^pay/edit/(?P<id>\d+)/?$' , pv.pay_edit, {
        'vtemplate': 'pay_edit.html'}),
    # last pay's
    (r'^pay/last/$' , pv.pay_last, {
        'vtemplate': 'pay_last.html'}),
    # delete pay
    (r'^pay/del/(?P<id>\d+)/?$' , pv.pay_del, {
        'vtemplate': 'pay_add.html'}),
    # add correct pay
    (r'^pay/correct/$' , pv.pay_correct, {
        'vtemplate': 'pay_add.html'}),
    # view all user itypes
    (r'^types/$' , pv.itypes_all, {
            'vtemplate': 'itype_all.html'}),
    # itype view, group by sing
    (r'^type/view/(?P<sign>\d+)/?$' , pv.itype_view, {
        'vtemplate': 'itype_view.html'}),
    # add itype
    (r'^type/add/$' , pv.itype_add, {
        'vtemplate': 'pay_add.html'}),
    # delete itype
    (r'^type/del/(?P<id>\d+)/?$' , pv.itype_del, {
        'vtemplate': 'pay_add.html'}),
    # edit itype
    (r'^type/edit/(?P<id>\d+)/?$' , pv.itype_edit, {
        'vtemplate': 'itype_edit.html'}),
    # delete itype
    (r'^transfer/update/$' , pv.transfer_update, {
        'vtemplate': 'transfer_update.html'}),
     # add transfer
    (r'^transfer/add/$' , pv.transfer_add, {
        'vtemplate': 'pay_add.html'}),
    # last transfer pay's
    (r'^transfer/last/$' , pv.transfer_last, {
        'vtemplate': 'transfer_last.html'}),
    # delete transfer
    (r'^transfer/del/(?P<id>\d+)/?$' , pv.transfer_del, {
        'vtemplate': 'pay_add.html'}),
    # edit transfer
    (r'^transfer/edit/(?P<id>\d+)/?$' , pv.transfer_edit, {
        'vtemplate': 'transfer_edit.html'}),
    # depts autocomplete 
    (r'^dept/complete/?$' , pv.dept_complete),
    # last depts
    (r'^depts/last/$' , pv.depts_last, {
        'vtemplate': 'depts_last.html'}),
     # add itype
    (r'^dept/add/$' , pv.dept_add, {
        'vtemplate': 'pay_add.html'}),
    # delete dept
    (r'^dept/del/(?P<id>\d+)/?$' , pv.dept_del, {
        'vtemplate': 'pay_add.html'}),
    # edit dept
    (r'^dept/edit/(?P<id>\d+)/?$' , pv.dept_edit, {
        'vtemplate': 'dept_edit.html'}),
    # history page
    (r'^history/$' , pv.history, {
        'vtemplate': 'history.html'}),
    # history result search
    (r'^history/update/$' , pv.history_update, {
        'vtemplate': 'history_update.html'}),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

# media content                   
# urlpatterns += patterns('',) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^robots.txt$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'path': "robots.txt"}),
        url(r'^favicon.ico$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'path': "favicon.ico"}),
   )
    # urlpatterns += patterns('django.contrib.staticfiles.views',
    #     url(r'^static/(?P<path>.*)$', 'serve'),
    # )
