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
    # view all user itypes
    (r'^types/$' , pv.itypes_all, {
            'vtemplate': 'itype_all.html'}),
    # itype view, group by sing
    (r'^type/view/(?P<sign>\d+)/?$' , pv.itype_view, {
        'vtemplate': 'itype_view.html'}),

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
