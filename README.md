# Πρόγραμμα myf

Δημιουργία και ανέβασμα καταστάσεων ΜΥΦ

Το πρόγραμμα υποστηρίζει τη δημιουργία καταστάσεων ΜΥΦ (μόνο έσοδα)
και το ανέβασμά τους στο TAXIS, σε δύο διακριτά βήματα.

Τα στοιχεία τιμολογίων πρέπει να είναι διαθέσιμα σε ένα αρχείο CSV
της μορφής:

    <Α/Α>,<ΑΦΜ>,<ΕΕΕΕ-ΜΜ-ΗΗ>,<ΑΞΙΑ>,<%ΦΠΑ>

Παράδειγμα:

    17,998765432,2017-01-30,1030.5,0.24
    18,998765432,2017-02-21,900,0.13

Το αρχείο ρυθμίσεων σε μορφή JSON πρέπει να περιλαμβάνει τα εξής:

    {"afm": "το_ΑΦΜ_σου",
     "username": "Κωδικός εισόδου ΜΥΦ",
     "password": "Συνθηματικό ΜΥΦ"}

Ο κωδικός εισόδου ΜΥΦ και το συνθηματικό ΜΥΦ εκδίδονται στη σελίδα:
https://www1.gsis.gr/sgsisapps/tokenservices

## Εγκατάσταση

Για εγκατάσταση δώστε την εντολή:

    python setup.py install

Σε Debian/Ubuntu, εγκαταστείστε τις εξαρτήσεις με:

    apt-get install python-lxml python-stdnum python-requests

## Copyright and license

Copyright (C) 2017-2018 Giorgos Korfiatis <korfiatis@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
