#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2017-2018 Giorgos Korfiatis <korfiatis@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import datetime
import argparse
from collections import namedtuple
import csv
import json
from lxml import etree
import stdnum.gr.vat
import os
import requests
import zipfile
import StringIO

Entry = namedtuple("Entry",
                   ["id", "afm", "date", "amount", "fpa_rate"])


schema_s = b"""<?xml version="1.0" encoding="utf-8"?>
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="afm-type">
    <xs:restriction base="xs:string">
      <xs:pattern value="\d{9}"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="decimal-type" >
    <xs:restriction base="xs:string">
      <xs:maxLength value="19" />
      <xs:pattern value="\d{1,16}(,\d{1,2})?"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="decimal-type2" >
    <xs:restriction base="xs:string">
      <xs:maxLength value="19" />
      <xs:pattern value="[+-]?\d{1,15}(,\d{1,2})?"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="year-type" >
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="1900"/>
      <xs:maxInclusive value="2999"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="month-type" >
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="1"/>
      <xs:maxInclusive value="12"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="action-type">
    <xs:restriction base="xs:string">
      <xs:enumeration value="replace"/>
      <xs:enumeration value="incremental"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="note-type">
    <xs:restriction base="xs:string">
      <xs:enumeration value="credit"/>
      <xs:enumeration value="normal"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="nonObl-type" >
    <xs:restriction base="xs:integer">
      <xs:minInclusive value="0"/>
      <xs:maxInclusive value="1"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="packages">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="package" minOccurs="1" maxOccurs="1">
          <xs:complexType>
            <xs:all>
              <xs:element name="revenueInvoices" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="invoice" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="afm" type="afm-type" />
                          <xs:element name="unique_id" type="xs:string" minOccurs="0"/>
                          <xs:element name="amount" type="decimal-type" />
                          <xs:element name="tax" type="decimal-type" />
                          <xs:element name="note" type="note-type" />
                          <xs:element name="date" type="xs:date" />
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
              <xs:element name="groupedRevenues" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="revenue" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="afm" type="afm-type" />
                          <xs:element name="amount" type="decimal-type" />
                          <xs:element name="tax" type="decimal-type" />
                          <xs:element name="invoices" type="xs:positiveInteger" />
                          <xs:element name="note" type="note-type" />
                          <xs:element name="date" type="xs:date" minOccurs="0"/>
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
              <xs:element name="groupedExpenses" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="expense" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="afm" type="afm-type" />
                          <xs:element name="amount" type="decimal-type" />
                          <xs:element name="tax" type="decimal-type" />
                          <xs:element name="invoices" type="xs:positiveInteger" />
                          <xs:element name="note" type="note-type" />
                          <xs:element name="nonObl" type="nonObl-type" />
                          <xs:element name="date" type="xs:date" minOccurs="0"/>
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
              <xs:element name="groupedCashRegisters" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="cashregister" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="cashreg_id" type="xs:string" minOccurs="0"/>
                          <xs:element name="amount" type="decimal-type2" />
                          <xs:element name="tax" type="decimal-type2" />
                          <xs:element name="date" type="xs:date" minOccurs="0"/>
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
              <xs:element name="otherExpenses" minOccurs="0">
                <xs:complexType>
                  <xs:all>
                    <xs:element name="amount" type="decimal-type2" />
                    <xs:element name="tax" type="decimal-type2" />
                    <xs:element name="date" type="xs:date" minOccurs="0"/>
                  </xs:all>
                </xs:complexType>
              </xs:element>
              <xs:element name="casRevenues" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="casRevenue" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="afm" type="afm-type" />
                          <xs:element name="amount" type="decimal-type" />
                          <xs:element name="tax" type="decimal-type" />
                          <xs:element name="note" type="note-type" />
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
              <xs:element name="casExpenses" minOccurs="0">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="casExpense" maxOccurs="unbounded">
                      <xs:complexType>
                        <xs:all>
                          <xs:element name="afm" type="afm-type" />
                          <xs:element name="amount" type="decimal-type" />
                          <xs:element name="tax" type="decimal-type" />
                          <xs:element name="note" type="note-type" />
                        </xs:all>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                  <xs:attribute name="action" type="action-type" use="required" />
                </xs:complexType>
              </xs:element>
            </xs:all>
            <xs:attribute name="actor_afm" type="afm-type" use="required" />
            <xs:attribute name="month" type="month-type" use="required" />
            <xs:attribute name="year" type="year-type" use="required" />
            <xs:attribute name="branch" type="xs:string" use="optional" />
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""


def load_schema(s):
    schema_doc = etree.fromstring(s)
    return etree.XMLSchema(schema_doc)


SCHEMA = load_schema(schema_s)


def abort(s):
    print s
    print "Ματαιώθηκε."
    exit(1)


def _partition_by(f, l):
    d = {}
    for x in l:
        group = f(x)
        group_l = d.get(group, [])
        group_l.append(x)
        d[group] = group_l
    return d


def number(n):
    return str(n).replace(".", ",")


def register_invoice(revenue_invoices, entry):
    invoice = etree.SubElement(revenue_invoices, "invoice")
    etree.SubElement(invoice, "afm").text = entry.afm
    etree.SubElement(invoice, "unique_id").text = str(entry.id)
    etree.SubElement(invoice, "amount").text = number(entry.amount)
    fpa = entry.amount * entry.fpa_rate
    etree.SubElement(invoice, "tax").text = number(fpa)
    etree.SubElement(invoice, "note").text = "normal"
    etree.SubElement(invoice, "date").text = entry.date.isoformat()


def register_group(grouped_revenues, afm, amount, fpa, invoices, date):
    revenue = etree.SubElement(grouped_revenues, "revenue")
    etree.SubElement(revenue, "afm").text = afm
    etree.SubElement(revenue, "amount").text = number(amount)
    etree.SubElement(revenue, "tax").text = number(fpa)
    etree.SubElement(revenue, "invoices").text = str(invoices)
    etree.SubElement(revenue, "note").text = "normal"
    etree.SubElement(revenue, "date").text = date.isoformat()


def record_per_afm(revenue_invoices, grouped_revenues, afm, entries):
    assert entries
    entries = sorted(entries, key=lambda e: e.date)
    amount_sum = 0
    fpa_sum = 0
    ref_date = None
    for entry in entries:
        assert afm == entry.afm
        register_invoice(revenue_invoices, entry)
        amount_sum += entry.amount
        fpa_sum += entry.amount * entry.fpa_rate
        ref_date = entry.date
    assert ref_date
    register_group(
        grouped_revenues, afm, amount_sum, fpa_sum, len(entries), ref_date)


def myf_filename(actor_afm, categ, year, month):
    return "MYF_%s_%s_%s_%02d.xml" % (actor_afm, categ, year, month)


def mk_block(actor_afm, year, month, kind):
    doc = etree.Element("packages")
    package = etree.SubElement(
        doc, "package",
        actor_afm=actor_afm, month=str(month), year=str(year))
    block = etree.SubElement(package, kind, action="replace")
    return doc, block


def make_month_package(actor_afm, dest, year, month, entries):
    for entry in entries:
        assert entry.date.year == year and entry.date.month == month

    invoices_doc, revenue_invoices = mk_block(
        actor_afm, year, month, "revenueInvoices")
    grouped_doc, grouped_revenues = mk_block(
        actor_afm, year, month, "groupedRevenues")

    entries_per_afm = _partition_by(lambda entry: entry.afm, entries)
    for afm, afm_entries in entries_per_afm.iteritems():
        record_per_afm(revenue_invoices, grouped_revenues, afm, afm_entries)

    postprocess(actor_afm, dest, year, month, invoices_doc, "INV")
    postprocess(actor_afm, dest, year, month, grouped_doc, "GRO")


def postprocess(actor_afm, dest, year, month, doc, tag):
    validate_xml(doc)
    filename = myf_filename(actor_afm, tag, year, month)
    to_file(dest, filename, doc)


def to_file(dest, filename, doc):
    filepath = os.path.join(dest, filename)
    with open(filepath, "w") as f:
        f.write(etree.tostring(doc, pretty_print=True))
    print "Αποθήκευση %s" % filename


def make_year_packages(actor_afm, dest, year, entries):
    for month, month_entries in _partition_by(
            lambda entry: entry.date.month, entries).iteritems():
        make_month_package(actor_afm, dest, year, month, month_entries)


def create_myf(actor_afm, dest, entries):
    for year, year_entries in _partition_by(
            lambda entry: entry.date.year, entries).iteritems():
        make_year_packages(actor_afm, dest, year, year_entries)


def read_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        abort("Λανθασμένη ημερομηνία '%s'." % s)


def validate_afm(afm):
    try:
        stdnum.gr.vat.validate(afm)
    except:
        abort("Μη έγκυρο ΑΦΜ '%s'." % afm)


def validate_entries(entries):
    prev = None
    for entry in entries:
        validate_afm(entry.afm)
        if prev:
            if entry.id <= prev.id:
                abort("Εγγραφή %s εκτός σειράς." % entry.id)
            if entry.date < prev.date:
                abort("Εγγραφή με ημερομηνία %s εκτός σειράς." % entry.date)
        prev = entry


def read_from_file(filename):
    entries = []
    with open(filename) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            entry = Entry(id=row[0],
                          afm=row[1],
                          date=read_date(row[2]),
                          amount=float(row[3]),
                          fpa_rate=float(row[4]))
            entries.append(entry)
    return entries


def validate_xml(xmldoc):
    print "Έλεγχος εγκυρότητας..."
    try:
        SCHEMA.assertValid(xmldoc)
    except Exception as e:
        abort("Άκυρο αρχείο xml: %s." % e)


def generate(settings, csvfile, dest=None):
    actor_afm = get_setting(settings, "afm")
    validate_afm(actor_afm)
    entries = read_from_file(csvfile)
    validate_entries(entries)
    if dest is None:
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
        dest = "MYF-%s" % now
    os.makedirs(dest)
    create_myf(actor_afm, dest, entries)
    print "Οι καταστάσεις ΜΥΦ αποθηκεύτηκαν στον φάκελο '%s'." % dest


def show_list(lst):
    return ", ".join(map(str, lst))


def validate_quarter(entries):
    years = set(entry.date.year for entry in entries)
    if len(years) != 1:
        abort("Οι καταστάσεις αναφέρονται σε διαφορετικά έτη: %s"
              % show_list(years))
    year = years.pop()
    quarters = set(1 + (entry.date.month - 1) // 3 for entry in entries)
    if len(quarters) != 1:
        abort("Οι καταστάσεις αναφέρονται σε διαφορετικά τρίμηνα: %s"
              % show_list(quarters))
    quarter = quarters.pop()
    return year, quarter


def f2_per_fpa_rate(fpa_rate, entries):
    sum_amount = 0
    for entry in entries:
        sum_amount += entry.amount
        assert fpa_rate == entry.fpa_rate
    fpa = fpa_rate * sum_amount
    return sum_amount, fpa


def f2(settings, csvfile):
    entries = read_from_file(csvfile)
    validate_entries(entries)
    year, quarter = validate_quarter(entries)
    print "Στοιχεία Φ2 για έτος: %s τρίμηνο: %s." % (year, quarter)
    for fpa_rate, entries_per_fpa_rate in _partition_by(
            lambda entry: entry.fpa_rate, entries).iteritems():
        sum_amount, fpa = f2_per_fpa_rate(fpa_rate, entries_per_fpa_rate)
        print "Κατηγορία: %s Αξία: %s ΦΠΑ: %s" % (
            fpa_rate, number(sum_amount), number(fpa))

URL = "https://www1.gsis.gr/myf/oltp/api/post/file"


def zip_file(filepath, arcname):
    s = StringIO.StringIO()
    z = zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED)
    z.write(filepath, arcname=arcname)
    z.close()
    return s.getvalue()


def get_logger(f):
    def log(msg):
        print msg
        msgln = msg + '\n'
        msgln = msgln.encode('utf-8')
        f.write(msgln)
    return log


def upload(settings, dirname):
    username = get_setting(settings, "username")
    password = get_setting(settings, "password")
    log_file = os.path.join(dirname, 'upload.log')
    if os.path.exists(log_file):
        abort(
            "Φαίνεται ότι τα αρχεία έχουν ήδη ανέβει. "\
            "Αν θέλεις να τα ανεβάσεις, μετακίνησε το αρχείο '%s'." %
            log_file)

    with open(log_file, 'w') as f:
        log = get_logger(f)
        log("Έναρξη: %s" % datetime.datetime.now())
        for filename in os.listdir(dirname):
            if not filename.endswith('.xml'):
                continue
            upload_file(username, password, dirname, filename, log)
        log("Λήξη: %s" % datetime.datetime.now())


def upload_file(username, password, dirname, filename, log):
    filepath = os.path.join(dirname, filename)
    log("Ανέβασμα αρχείου: %s" % filepath)
    zip_filename = "%s.zip" % filename
    files = {"file": (zip_filename,
                      zip_file(filepath, filename),
                      "application/octet-stream")}
    r = requests.post(URL, files=files, auth=(username, password))
    log("Απάντηση: %s" % r.status_code)
    log(r.content)


def get_setting(settings, key):
    try:
        return settings[key]
    except KeyError:
        abort("Λείπει η ρύθμιση '%s'." % key)


def read_settings(filename):
    if not os.path.exists(filename):
        abort("Δεν υπάρχει το αρχείο '%s'." % filename)
    with open(filename) as f:
        return json.load(f)


DEFAULT_SETTINGS_FILE = "~/.myfrc"
EXPANDED_DEFAULT_SETTINGS_FILE = os.path.expanduser(DEFAULT_SETTINGS_FILE)

description = """Δημιουργία και ανέβασμα καταστάσεων ΜΥΦ

Το πρόγραμμα υποστηρίζει τη δημιουργία καταστάσεων ΜΥΦ (μόνο έσοδα)
και το ανέβασμά τους στο TAXIS, σε δύο διακριτά βήματα.

Τα στοιχεία τιμολογίων πρέπει να είναι διαθέσιμα σε ένα αρχείο CSV
της μορφής: <Α/Α>,<ΑΦΜ>,<ΕΕΕΕ-ΜΜ-ΗΗ>,<ΑΞΙΑ>,<%ΦΠΑ>
Παράδειγμα:
  17,998765432,2017-01-30,1030.5,0.24
  18,998765432,2017-02-21,900,0.13

Το αρχείο ρυθμίσεων σε μορφή JSON πρέπει να περιλαμβάνει τα εξής:
  {"afm": "το_ΑΦΜ_σου",
   "username": "Κωδικός εισόδου ΜΥΦ",
   "password": "Συνθηματικό ΜΥΦ"}

Ο κωδικός εισόδου ΜΥΦ και το συνθηματικό ΜΥΦ εκδίδονται στη σελίδα:
https://www1.gsis.gr/sgsisapps/tokenservices"""


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument(
        '--settings', metavar='JSON', default=EXPANDED_DEFAULT_SETTINGS_FILE,
        help='Αρχείο ρυθμίσεων (προκαθορισμένο: %s)' % DEFAULT_SETTINGS_FILE)
    parser.add_argument(
        '--generate', metavar='CSV',
        help='Δημιουργία καταστάσεων ΜΥΦ από αρχείο CSV')
    parser.add_argument(
        '--f2', metavar='CSV',
        help='Δημιουργία κατάστασης Φ2 από αρχείο CSV')
    parser.add_argument('--upload', metavar='DIR',
                        help='Ανέβασμα καταστάσεων ΜΥΦ από φάκελο')
    args = parser.parse_args()
    if not(bool(args.generate) ^ bool(args.upload) ^ bool(args.f2)):
        abort("Πρέπει να διαλέξεις είτε 'generate' είτε 'upload' είτε 'f2'.")

    settings_file = args.settings
    settings = read_settings(settings_file)
    if args.generate:
        generate(settings, args.generate)
    if args.f2:
        f2(settings, args.f2)
    if args.upload:
        upload(settings, args.upload)

if __name__ == "__main__":
    main()
