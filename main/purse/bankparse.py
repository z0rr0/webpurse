#-*- coding: utf-8 -*-
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import datetime, os

RUB_IDX = 643
# fn = '/home/zorro/gitrep/djcode/webpurse/purse/bank.xml'

def import_xml_dom(filename):
    if not os.path.isfile(filename):
        return False

    def get_text(node_list):
        text =[]
        for node in node_list:
            if node.nodeType == node.TEXT_NODE:
                text.append(node.data)
        return "".join(text).strip()
    try:
        dom = minidom.parse(filename)
    except (EnvironmentError, ExpatError) as err:
        print "Error: %s" % err
        return False
    
    def nom2kurs(nominal, value):
        try:
            count_money = int(nominal)
            count_k = float(value.replace(",", "."))
            return count_k / count_money
        except ValueError:
            return 0
    
    # self.clean()
    fordate = dom.getElementsByTagName("ValCurs")[0]
    fordate = datetime.datetime.strptime(fordate.getAttribute("Date"), "%d.%m.%Y").date()
    data = {}
    valutes = dom.getElementsByTagName("Valute")
    for valute in valutes:
        try:
            ind = valute.getAttribute("ID")
            data[ind] = {}
            tmp = valute.getElementsByTagName("NumCode")[0]
            data[ind]["id"] = get_text(tmp.childNodes)
            tmp = valute.getElementsByTagName("CharCode")[0]
            data[ind]["code"] = get_text(tmp.childNodes)
            tmp = valute.getElementsByTagName("Name")[0]
            data[ind]["name"] = get_text(tmp.childNodes)
            tmp = valute.getElementsByTagName("Nominal")[0]
            nominal = get_text(tmp.childNodes)
            tmp = valute.getElementsByTagName("Value")[0]
            value = get_text(tmp.childNodes)
            data[ind]["kurs"] = nom2kurs(nominal, value)
            data[ind]["date"] = fordate
        except (ValueError, LookupError) as err:
            print "Error: %s" % err
            return False
    # add ruble
    ind = RUB_IDX
    data[ind] = {}
    data[ind]["id"] = ind
    data[ind]["code"] = 'RUB'
    data[ind]["name"] = u'Российский рубль'
    data[ind]["kurs"] = 1.0
    data[ind]["date"] = datetime.datetime.now()
    # result
    return data
 
# k = import_xml_dom(fn)
# print k