###MODEL

import urllib.request, json
from datetime import datetime, timedelta, date
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki
import auth_public as auth
import sys
import bcrypt
import time
import sqlite3
import psycopg2, psycopg2.extensions, psycopg2.extras
from psycopg2 import sql, Error
import os

# UVOZ VSEH PAKETOV, KI JIH POTREBUJEMO


# SLOVAR ZA PRETVORBO IZ KRATIC V IMENA PODJETIJ

IMENA_PODJETIJ = {
    "CICG": "Cinkarna Celje", "IEKG": "Intereuropa", "KRKG": "Krka", "LKPG": "Luka Koper",
    "MELR": "Mercator", "NLBR": "NLB", "PETG": "Petrol", "POSR": "Pozavarovalnica Sava",
    "TLSG": "Telekom Slovenije", "ZVTG": "Zavarovalnica Triglav", "CETG": "Cetis",
    "DATG": "Datalab tehnologije", "DPRG": "Delo prodaja", "GHUR": "Union Hotels Collection",
    "KDHR": "KD Group", "KSFR": "KS Naložbe", "MKOG": "Melamin", "MTSG": "Kompas MTS",
    "NALN": "Nama", "NIKN": "Nika", "PPDT": "Prva Group", "SALR": "Salus", "SKDR": "KD",
    "TCRG": "Terme Čatež", "UKIG": "Unior", "VHDR": "Vipa Holding"
}



# Preberemo port za bazo iz okoljskih spremenljivk
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)



# Funkcija za ustvarjanje povezave z bazo
def create_connection():
    try:

        connection = psycopg2.connect(

            database=auth.db, 
            host=auth.host, 
            user=auth.user, 
            password=auth.password, 
            port=DB_PORT
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


#ZA STRAN STATITSTIKO PRIDOBI PODATKE GLEDE NA ČASOVNO OBDOBJE IN NATANČNOST

def poizvej_podatke(simbol, natancnost, zacetek, konec):
    conn = create_connection()
    cursor = conn.cursor()

    if natancnost == 'tedensko':#IZBERE TEDENSKI IZBOR, PRI DATUMU DODA KRATICO -T, DA POUDARI ZA KATERI TEDEN GRE
        group_field = "EXTRACT(YEAR FROM datum) || '-T' || TO_CHAR(datum, 'IW')"
    elif natancnost == 'mesecno':#IZBERE MESEČNI IZBOR, PRI DATUMU DODA KRATICO -M, DA POUDARI ZA KATERI MESEC GRE
        group_field = "EXTRACT(YEAR FROM datum) || '-M' || TO_CHAR(datum, 'MM')"
    else:#NAREDI POIZVEDBO PO DNEVIH
        cursor.execute(f"""
        SELECT
            datum AS obdobje,
            vrednost AS vrednosti
        FROM vrednosti_od_papirjev
        WHERE oznaka = %s
          AND datum BETWEEN %s AND %s
        ORDER BY 1;
        """, (simbol, zacetek, konec))
        rezultati = cursor.fetchall()
        conn.close()

        obdobja = [r[0].strftime("%Y-%m-%d") for r in rezultati]
        vrednosti = [float(r[1]) for r in rezultati]
        return obdobja, vrednosti
    
    # NAREDI POIZVEDBO PO TEDNIH ALI MESECIH, TER POIŠČE POVPREČJE TSITEGA MESECA ALI TEDNA
    query = f""" 
        SELECT
            {group_field} AS obdobje,
            ROUND(AVG(vrednost), 2) AS vrednosti
        FROM vrednosti_od_papirjev
        WHERE oznaka = %s
          AND datum BETWEEN %s AND %s
        GROUP BY 1
        ORDER BY 1;
    """

    cursor.execute(query, (simbol, zacetek, konec))
    rezultati = cursor.fetchall()
    conn.close()

    obdobja = [r[0] for r in rezultati]
    vrednosti = [float(r[1]) for r in rezultati]
    return obdobja, vrednosti


def portfelj_po_dnevih(uporabnik):
    """
    Vrne datume in vrednosti portfelja uporabnika po dnevih.
    Vrednost se izračuna kot vsota (kolicina * cena papirja na dan)
    """
    conn = create_connection()
    cursor = conn.cursor()

    query = """
    WITH kumulativne_kolicine AS (
        SELECT
            p.id_uporabnika,
            v.datum,
            p.kratica,
            SUM(p.kolicina) AS kolicina
        FROM
            portfeljske_transakcije p
        JOIN
            vrednosti_od_papirjev v ON v.oznaka = p.kratica
        WHERE
            p.id_uporabnika = %s
            AND p.datum_transakcije <= v.datum
        GROUP BY
            p.id_uporabnika, v.datum, p.kratica
    ),
    vrednosti_portfelja AS (
        SELECT
            k.id_uporabnika,
            k.datum,
            SUM(k.kolicina * v.vrednost) AS skupna_vrednost
        FROM
            kumulativne_kolicine k
        JOIN
            vrednosti_od_papirjev v ON v.oznaka = k.kratica AND v.datum = k.datum
        GROUP BY
            k.id_uporabnika, k.datum
    )
    SELECT
        datum,
        ROUND(skupna_vrednost, 2) AS portfelj
    FROM vrednosti_portfelja
    ORDER BY datum;
    """

    try:
        cursor.execute(query, (uporabnik,))
        rezultati = cursor.fetchall()
    except Exception as e:
        print("Napaka pri pridobivanju dnevne vrednosti portfelja:", e)
        rezultati = []

    conn.close()

    datumi = [r[0].strftime("%Y-%m-%d") for r in rezultati]
    vrednosti = [float(r[1]) for r in rezultati]
    return datumi, vrednosti

    
def struktura_portfelja(uporabnik, danes=None):
    """
    Vrne seznam (ime papirja, vrednost_papirja) in skupno vsoto za posamezno delnico glede na trenutno stanje.
    """
    if danes is None:
        danes = date.today()

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        p.kratica,
        SUM(p.kolicina) AS skupna_kolicina,
        v.vrednost,
        SUM(p.kolicina) * v.vrednost AS vrednost_papirja
    FROM portfeljske_transakcije p
    JOIN (
        SELECT DISTINCT ON (oznaka) oznaka, vrednost
        FROM vrednosti_od_papirjev
        WHERE datum <= %s
        ORDER BY oznaka, datum DESC
    ) v ON v.oznaka = p.kratica
    WHERE p.id_uporabnika = %s
    GROUP BY p.kratica, v.vrednost
    HAVING SUM(p.kolicina) != 0
    ORDER BY vrednost_papirja DESC;
    """

    cursor.execute(query, (danes, uporabnik))
    podatki = cursor.fetchall()
    conn.close()

    podatki = [
    (IMENA_PODJETIJ.get(row[0], row[0]), row[1], row[2], row[3])
    for row in podatki
]

    # rezultat: [(KRKG, 10, 86.2, 862.0), ...]
    return podatki




class vlagatelj:

    def __init__(self, ime=None, geslo=None, rola=None):
            self.ime = ime
            self.geslo = geslo
            #self.rola = 

            
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
        
        hashed_password = bcrypt.hashpw(self.geslo.encode('utf-8'), bcrypt.gensalt())

        cursor.execute("INSERT INTO uporabnik (ime, geslo) VALUES (%s, %s)", (self.ime, hashed_password.decode('utf-8')))
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

        if result:
            stored = result[0]

            try:

                if stored.startswith("$2b$") or stored.startswith("$2a$"):
                    return bcrypt.checkpw(geslo.encode('utf-8'), stored.encode('utf-8'))
                else:

                    if stored == geslo:

                        hashed = bcrypt.hashpw(geslo.encode('utf-8'), bcrypt.gensalt())
                        conn = create_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE uporabnik SET geslo = %s WHERE ime = %s", (hashed.decode('utf-8'), self.ime))
                        conn.commit()
                        conn.close()
                        return True
            except Exception as e:
                print("Napaka pri preverjanju gesla:", e)
                return False

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


