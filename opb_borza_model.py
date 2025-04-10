###MODEL

import urllib.request, json
from datetime import datetime, timedelta
import sys
import time
import sqlite3
import psycopg2, psycopg2.extensions, psycopg2.extras
from psycopg2 import sql, Error

def create_connection():
    try:
        connection = psycopg2.connect(
            user='rokl',
            password='skn6t66w',
            host='baza.fmf.uni-lj.si', 
            #port='8080',       
            database='sem2024_rokl'
        )
        return connection
    except Error as e:
        print(f"Error: '{e}' occurred while connecting to the database")
        return None

url = 'https://rest.ljse.si/web/Bvt9fe2peQ7pwpyYqODM/price-list/XLJU/'#+str(danasnji_dan)+'/json'

def danasnji_dan():#Ne vem tocno, kdaj posodobijo podatke, po izkušnjah pa so ob 17h bili posodobljeni, zato če je ura pred 17h, dan zamaknem nazaj
    if datetime.today().time().hour < 17 and datetime.today().weekday() == 6:#podatkov ne posodabljajo zjutraj
        datum = datetime.today()-timedelta(days=2)
    elif datetime.today().time().hour < 17 and datetime.today().weekday() == 5:#podatkov ne posodabljajo zjutraj
        datum = datetime.today()-timedelta(days=1)
    elif datetime.today().time().hour < 17 and datetime.today().weekday() == 0:#danasnji dna pnedeljek, ura manj kot 17h
        datum = datetime.today()-timedelta(days=3)#nastavi na petek prejsnji teden    
    elif datetime.today().time().hour >= 17:
        if datetime.today().weekday() == 6:
            datum = datetime.today()-timedelta(days=2)
        elif datetime.today().weekday() == 5:
            datum = datetime.today()-timedelta(days=1)
        else:
            datum = datetime.today()
    else:
        datum = datum = datetime.today()-timedelta(days=1)
    return datum.date()

def izbrani_datum(dan):#sobote in nedelje zmakne na petek
    if datetime.strptime(dan.replace(' ',''), '%d.%m.%Y').weekday() == 6:
        izbrani_dan = datetime.strptime(dan.replace(' ',''), '%d.%m.%Y')-timedelta(days=2)
    elif datetime.strptime(dan.replace(' ',''), '%d.%m.%Y').weekday() == 5:
        izbrani_dan = datetime.strptime(dan.replace(' ',''), '%d.%m.%Y')-timedelta(days=1)
    else:
        izbrani_dan = datetime.strptime(dan.replace(' ',''), '%d.%m.%Y')
    return izbrani_dan.date()

#########
#fetch data spremeniš datum iz današnji dan na izbrani dan

def fetch_data_from_api():
    datum = danasnji_dan()
    url = f'https://rest.ljse.si/web/Bvt9fe2peQ7pwpyYqODM/price-list/XLJU/{datum}/json'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data

def fetch_data_for_date(date):
    try:
        url = f'https://rest.ljse.si/web/Bvt9fe2peQ7pwpyYqODM/price-list/XLJU/{date}/json'
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        return data
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return None
        else:
            return None




def get_latest_date():
    conn = create_connection()
    if conn is None:
        return datetime.strptime('03.01.2018', '%d.%m.%Y')#03.01.2018->danasnji dan

    cursor = conn.cursor()
    cursor.execute("SELECT MAX(datum) FROM vrednosti_od_papirjev")
    result = cursor.fetchone()
    conn.close()

    if result and result[0] is not None:
        return datetime.strptime(str(result[0]), '%Y-%m-%d')
        
    else:
        return datetime.strptime('03.01.2018', '%d.%m.%Y')

def get_date_range(start_date, end_date):
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    return date_range



def date_exists_in_database(date):
    conn = create_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM vrednosti_od_papirjev WHERE datum = %s", (date,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
def save_data_to_database(data, date):
    conn = create_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    for security in data['securities']:
        id_papirja = security['symbol']
        vrednost = security['close_price']
        if vrednost is not None:
            cursor.execute('''
                INSERT INTO vrednosti_od_papirjev (oznaka, datum, vrednost)
                VALUES (%s, %s, %s)
            ''', (id_papirja, date, vrednost))
    
    conn.commit()
    conn.close()


def main(selected_date):
    start_date = get_latest_date()
    end_date = datetime.strptime(str(selected_date), '%Y-%m-%d')
    
    date_range = get_date_range(start_date, end_date)
    
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        if not date_exists_in_database(date_str):
            data = fetch_data_for_date(date_str)
            if data:
                save_data_to_database(data, date_str)


def dodaj_vrednosti(oznaka):
    conn = create_connection()
    if conn is None:
        print("Povezava ni bila uspešno vzpostavljena.")
    else:
        try:
            cursor = conn.cursor()
            cursor.execute('''SELECT "datum", "vrednost" FROM "public"."vrednosti_od_papirjev" WHERE "oznaka" = %s''', (oznaka,))
            result = cursor.fetchall()
            print(result)
        except Exception as e:
            print(f"Napaka pri izvajanju poizvedbe: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return result


def pretvori_rezultat_v_seznama(rezultat):
    datumi = []
    vrednosti = []

    # Pretvori rezultat v dva ločena seznama
    for datum, vrednost in rezultat:
        formatiran_datum = datum.strftime('%Y-%m-%d')
        datumi.append(formatiran_datum)
        vrednosti.append(float(vrednost))  

    return datumi, vrednosti



def ustvari_obdobje(zacetek, konec, datumi, vrednosti):
    ustrezni_datumi = []
    ustrezne_vrednosti = []
    
    # Pretvori začetni in končni datum v datetime objekte
    zacetek = datetime.strptime(zacetek, "%d.%m.%Y")  # Popravljeno na %Y
    konec = datetime.strptime(konec, "%d.%m.%Y")  # Popravljeno na %Y
    
    # Pretvori vse datume v seznamu v datetime objekte
    datumi_objekti = [datetime.strptime(datum, "%Y-%m-%d") for datum in datumi]  # Popravljeno na %Y
    
    # Preveri, če dolžina seznamov datumi in vrednosti ustreza
    if len(datumi_objekti) != len(vrednosti):
        raise ValueError("Seznami datumi in vrednosti morajo biti enake dolžine")
    
    # Filtriraj ustrezne datume in vrednosti
    for datum, vrednost in zip(datumi_objekti, vrednosti):
        if zacetek <= datum <= konec:
            ustrezni_datumi.append(datum.strftime("%Y-%m-%d"))
            ustrezne_vrednosti.append(vrednost)
    
    return ustrezni_datumi, ustrezne_vrednosti

def doloci_frekvenco_podatkov(natancnost, datumi, vrednosti):
    koncni_datumi = []
    koncne_vrednosti = []
    if natancnost == 'mesecno':
        for i in range(len(datumi)):
            if i % 22 == 0:
                koncni_datumi.append(datumi[i])
                koncne_vrednosti.append(vrednosti[i])
        return koncni_datumi, koncne_vrednosti
    elif natancnost == 'tedensko':
        for i in range(len(datumi)):
            if i % 5 == 0:
                koncni_datumi.append(datumi[i])
                koncne_vrednosti.append(vrednosti[i])
        return koncni_datumi, koncne_vrednosti
    else:
        return datumi, vrednosti


class vlagatelj:

    def __init__(self, ime=None, geslo=None):
            self.ime = ime
            self.geslo = geslo
            
    def shrani_uporabnika(self):
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()

        cursor.execute("SELECT * FROM uporabnik WHERE ime = %s", (self.ime,))
        result = cursor.fetchone()

        if result:
            conn.close()
            return False  # User already exists

        cursor.execute("INSERT INTO uporabnik (ime, geslo) VALUES (%s, %s)", (self.ime, self.geslo))
        conn.commit()
        conn.close()
        return True

    def preveri_uporabnika(self, geslo):
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()

        cursor.execute("SELECT geslo FROM uporabnik WHERE ime = %s", (self.ime,))
        result = cursor.fetchone()

        conn.close()

        if result and result[0] == geslo:
            return True
        else:
            return False

    def dobi_podatke (self, datoteka):
        for i in range(len(datoteka)):
            if datoteka[i][0]==self.ime:
                return self



    def dodaj_v_dat(self, datoteka):
        datoteka.append(self)


    def get_user_id(self):
        conn = create_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT ime FROM uporabnik WHERE ime = %s", (self.ime,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return None

    def vnesi_transakcijo(self, st_papirjev, simbol, datum, opis=""):
        
        conn = create_connection()
        if conn is None:
            return False

        user_id = self.get_user_id()
        if user_id is None:
            conn.close()
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(kolicina) AS stanje FROM portfeljske_transakcije WHERE id_uporabnika = %s AND kratica = %s GROUP BY id_uporabnika, kratica", (user_id, simbol))
        stanje_db = cursor.fetchone()
        if stanje_db:
            stanje = stanje_db[0]
        else:
            stanje = 0

        stanje = stanje + int(st_papirjev)
        
        if stanje >= 0:
            cursor.execute('''SELECT vrednost FROM vrednosti_od_papirjev WHERE oznaka = %s AND datum = %s
            ''', (simbol, datum))
            vrednost_db = cursor.fetchone()
            if vrednost_db:
                vrednost = vrednost_db[0]
            else:
                return False
            

            cursor.execute('''
                INSERT INTO portfeljske_transakcije (kratica, datum_transakcije, id_uporabnika, kolicina, opis, cena)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (simbol, str(datum), user_id, st_papirjev, opis, vrednost))
            conn.commit()
            conn.close()
        else:
            conn.close()
            return False



    def trenutni_portfelj(self):#izpiše simbol, št enot, današnja vrendost 
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute('''SELECT kratica, SUM(kolicina) AS total_kolicina, SUM(kolicina) * zadnja_vrednost.vrednost AS total_vrednost
                        FROM portfeljske_transakcije, zadnja_vrednost
                        WHERE portfeljske_transakcije.kratica = zadnja_vrednost.oznaka AND id_uporabnika = %s GROUP BY kratica, zadnja_vrednost.vrednost;''', (self.ime,))
        result = cursor.fetchall()
        return result
    
    def transakcije(self):
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute('''SELECT datum_transakcije, kratica, kolicina, cena, cena * kolicina AS vrednost 
                        FROM portfeljske_transakcije
                        WHERE id_uporabnika = %s;''', (self.ime,))
        result = cursor.fetchall()
        return result



    def stanje(self) :#vrednost portfelja
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute('''SELECT SUM(total_kolicina * vrednost) AS vrednost_portfelja
            FROM uporabnikov_portfelj
            WHERE id_uporabnika = %s;''', (self.ime,))
        result = cursor.fetchone()
        try:
            stanje_temp = round(float(result[0]),2)
        except:
            stanje_temp = 0
        
        return stanje_temp

        
        
    def vplacila(self):
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute('''SELECT SUM(kolicina * cena) AS vrednost_portfelja
            FROM portfeljske_transakcije
            WHERE id_uporabnika = %s and kolicina > 0;''', (self.ime,))
        result = cursor.fetchone()
        try:
            stanje_temp = round(float(result[0]),2)
        except:
            stanje_temp = 0
        
        return stanje_temp

    def izplacila(self):
        conn = create_connection()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute('''SELECT SUM(kolicina * cena) AS vrednost_portfelja
            FROM portfeljske_transakcije
            WHERE id_uporabnika = %s and kolicina < 0;''', (self.ime,))
        result = cursor.fetchone()
        try:
            stanje_temp = round(float(result[0]),2)
        except:
            stanje_temp = 0
        
        return stanje_temp


    def profit(self):#izplacila - vplacila + vrednost 
        profit = self.izplacila() - self.vplacila() + self.stanje()
        return profit
    
    def donosnost(self):#try zaradi možnosti praznega seznama transakcij->donosnost torej zaenkrat 0
        try:
            donosnost = round((self.profit() / self.vplacila()),2)
        except ZeroDivisionError:
            return 0.0
        return donosnost
    





    
def povprecje(datoteka):
    povprecje = 0
    skupna_donosnost = 0
    osebe = 0
    for oseba in datoteka:
        skupna_donosnost += oseba.donosnost(datoteka)
        osebe += 1
    return round((skupna_donosnost / osebe),2)








#metka = vlagatelj("metka1", "123", 10000)
#metka.trenutni_portfelj()


