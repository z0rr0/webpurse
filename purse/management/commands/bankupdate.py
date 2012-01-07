#-*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from webpurse.purse.bankparse import import_xml_dom
from webpurse.purse.models import Valuta
from webpurse.settings import BANK_FILE, BANK_LOG
from django.db import transaction
import datetime

def query_bank(filename):
    bankfile = import_xml_dom(BANK_FILE) 
    with transaction.commit_on_success():
        for key, value in bankfile.items():
            valuta, created = Valuta.objects.get_or_create(pk=value["id"])
            if created:
                valuta.name = value['name']
                valuta.code = value['code']
            valuta.date = value['date']
            valuta.kurs = value['kurs']
            valuta.save()
            # Valuta.objects.filter(id=value["id"]).update(
            #     code=value["code"], 
            #     date=value["date"],
            #     kurs=value["kurs"])
    return True

class Command(BaseCommand):
    # args = '<poll_id poll_id ...>'
    # help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        querb = query_bank(BANK_FILE)
        # querb = True
        try:
            nowd = str(datetime.datetime.now())
            if querb:
                fout = open(BANK_LOG, "w")
                fout.write("Import OK: " + nowd + "\n")
                fout.close()
                self.stdout.write('Successfully import bank file ' + nowd + ' \n')
            else:
                fout = open(BANK_LOG, "w")
                fout.write("Import error: " + nowd + "\n")
                fout.close()
                self.stdout.write('Error import bank file ' + nowd + ' \n')
        except (lOError, OSError) as err:
            print err
            