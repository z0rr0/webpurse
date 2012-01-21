from django.http import HttpResponse
import socket

def ping_test(request):
    s = socket.gethostname()
    return HttpResponse("<b>Pong!</b> Serven is works in <em>%s</em> host" % s)