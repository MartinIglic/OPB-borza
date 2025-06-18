from bottle import route, run, static_file, template, request, response, redirect
from opb_borza_model import vlagatelj
from opb_borza_model import *
import opb_borza_model
import psycopg2

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki
import auth_public as auth

IMENA_PODJETIJ = {
    "CICG": "Cinkarna Celje", "IEKG": "Intereuropa", "KRKG": "Krka", "LKPG": "Luka Koper",
    "MELR": "Mercator", "NLBR": "NLB", "PETG": "Petrol", "POSR": "Pozavarovalnica Sava",
    "TLSG": "Telekom Slovenije", "ZVTG": "Zavarovalnica Triglav", "CETG": "Cetis",
    "DATG": "Datalab tehnologije", "DPRG": "Delo prodaja", "GHUR": "Union Hotels Collection",
    "KDHR": "KD Group", "KSFR": "KS Naložbe", "MKOG": "Melamin", "MTSG": "Kompas MTS",
    "NALN": "Nama", "NIKN": "Nika", "PPDT": "Prva Group", "SALR": "Salus", "SKDR": "KD",
    "TCRG": "Terme Čatež", "UKIG": "Unior", "VHDR": "Vipa Holding"
}

# Database connection details
connection = psycopg2.connect(
    database=auth.db, 
    host=auth.host, 
    user=auth.user, 
    password=auth.password, 
    port=DB_PORT
)


#@route('/nov_uporabnik', method='POST')
#def nov_uporabnik():
#    uporabnik = request.forms.get('uporabnisko_ime')
#    geslo = request.forms.get('geslo')
#    rezultat = ''
#
#    if uporabnik == '' or geslo == '':
#        rezultat = 'Za kreiranje novega računa obvezno vnesite uporabniško ime in geslo.'
#    else:
#        try:
#            
#            with connection.cursor() as cursor:
#                cursor.execute("SELECT * FROM uporabnik WHERE ime = %s", (uporabnik,))
#                existing_user = cursor.fetchone()
#
#            if existing_user is None:
#                
#                with connection.cursor() as cursor:
#                    cursor.execute(
#                        "INSERT INTO uporabnik (ime, geslo) VALUES (%s, %s)",
#                        (uporabnik, geslo)
#                    )
#                    connection.commit()
#
#                
#                oseba = vlagatelj(uporabnik, geslo)
#                main(danasnji_dan())    
#                response.set_cookie('user', uporabnik)
#                return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
#                            transakcije=oseba.transakcije(), rezultat='Uporabnik uspešno kreiran.',
#                            donosnost=oseba.donosnost(), stanje=oseba.stanje())
#
#            else:
#                rezultat = 'Uporabnik s tem uporabniškim imenom že obstaja. Vnesite drugo ime.'
#
#        except Exception as e:
#            rezultat = f'Prišlo je do napake: {str(e)}'
#
#    return template('index_db_borza.html', rezultat=rezultat)


@route('/nov_uporabnik', method='POST')
def nov_uporabnik():
    uporabnik = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')
    rezultat = ''

    if uporabnik == '' or geslo == '':
        rezultat = 'Za kreiranje novega računa obvezno vnesite uporabniško ime in geslo.'
    else:
        oseba = vlagatelj(uporabnik, geslo)
        if oseba.shrani_uporabnika():
            main(danasnji_dan())    
            response.set_cookie('user', uporabnik)
            return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
                            transakcije=oseba.transakcije(), rezultat='Uporabnik uspešno kreiran.',
                            donosnost=oseba.donosnost(), stanje=oseba.stanje())
        else:
            rezultat = 'Uporabnik s tem uporabniškim imenom že obstaja. Vnesite drugo ime.'

    return template('index_db_borza.html', rezultat=rezultat)



#@route('/logiranje', method='POST')
#def logiranje():
#    uporabnik = request.forms.get('uporabnisko_ime')
#    geslo = request.forms.get('geslo')
#    try:
#        with connection.cursor() as cursor:
#            cursor.execute("SELECT * FROM uporabnik WHERE ime = %s AND geslo = %s", (uporabnik, geslo))
#            existing_user = cursor.fetchone()
#        if existing_user is None:
#            return template('index_db_borza.html', rezultat='Uporabnik s tem uporabniškim imenom in geslom ne obstaja.')
#        else:
#            response.set_cookie('user', uporabnik)
#            oseba = vlagatelj(uporabnik, geslo)
#            main(danasnji_dan())    
#            return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
#                            transakcije=oseba.transakcije(), rezultat='',
#                            donosnost=oseba.donosnost(), stanje=oseba.stanje())
#
#
#    except Exception as e:
#            rezultat = f'Prišlo je do napake: {str(e)}'
#    
#    return template('index_db_borza.html', rezultat=rezultat)


@route('/logiranje', method='POST')
def logiranje():
    uporabnik = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')

    oseba = vlagatelj(uporabnik, geslo)
    if oseba.preveri_uporabnika(geslo):
        main(danasnji_dan())    
        response.set_cookie('user', uporabnik)
        datumi, vrednosti = opb_borza_model.portfelj_po_dnevih(oseba.ime)
        spodnja_meja = min(vrednosti)
        zgornja_meja = max(vrednosti)
        struktura = opb_borza_model.struktura_portfelja(oseba.ime)
        skupna_vrednost = sum([float(r[3]) for r in struktura])
        labels = [IMENA_PODJETIJ.get(row[0], row[0]) for row in struktura]
        values = [round(float(row[3]), 2) for row in struktura]
        delezi = [round(100 * v / skupna_vrednost, 1) for v in values]
        oznake = [f"{label} ({d}%)" for label, d in zip(labels, delezi)]
        barve = [f"rgba({(i*47)%255}, {(i*83)%255}, {(i*61)%255}, 0.7)" for i in range(len(values))]

        return template('portfelj.html', 
                        ime_uporabnika=oseba.ime, 
                        podatki_uporabnika=oseba.trenutni_portfelj(),
                        transakcije=oseba.transakcije(), rezultat='',
                        donosnost=oseba.donosnost(), 
                        stanje=oseba.stanje(),
                        podatki_cas=datumi,
                        podatki_vrednost=vrednosti,
                        minimum=0.9 * spodnja_meja,
                        maximum=1.1 * zgornja_meja,
                        naslov_grafa=f"Portfelj uporabnika {oseba.ime}",
                        labels=labels,
                        vrednosti_tortni=values,
                        oznake=oznake,
                        barve=barve)
    else:
        return template('index_db_borza.html', rezultat='Uporabnik s tem uporabniškim imenom in geslom ne obstaja.')



@route('/', method='GET')
def index():
    return template('index_db_borza.html', rezultat='')


# Vnasanje nove transakcije
@route('/vnos', method='POST')
def vnos_post():
    rezultat = ''

    simbol = request.forms.get('simbol')
    vrsta_posla = request.forms.get('vrsta_posla')
    kolicina = request.forms.get('kolicina', type=int)
    if vrsta_posla == 'prodaja':
        kolicina = -kolicina

    datum = request.forms.get('datum')
    oseba_cookie = request.cookies.get('user')

    oseba = vlagatelj(oseba_cookie, None)
    
    try:
        opb_borza_model.izbrani_datum(datum)
    except ValueError:
        rezultat = 'Prosim vnesi veljaven datum'

    if rezultat == '':
        if oseba.vnesi_transakcijo(kolicina, simbol, datum) == False:
            rezultat = 'Vnos transakcije ni uspel.'
        else:
            rezultat = 'Vnos transakcije je uspel.'

    datumi, vrednosti = opb_borza_model.portfelj_po_dnevih(oseba.ime)
    spodnja_meja = min(vrednosti)
    zgornja_meja = max(vrednosti)
    struktura = opb_borza_model.struktura_portfelja(oseba.ime)
    skupna_vrednost = sum([float(r[3]) for r in struktura])
    labels = [IMENA_PODJETIJ.get(row[0], row[0]) for row in struktura]
    values = [round(float(row[3]), 2) for row in struktura]
    delezi = [round(100 * v / skupna_vrednost, 1) for v in values]
    oznake = [f"{label} ({d}%)" for label, d in zip(labels, delezi)]
    barve = [f"rgba({(i*47)%255}, {(i*83)%255}, {(i*61)%255}, 0.7)" for i in range(len(values))]
            
    return template('portfelj.html', 
                    ime_uporabnika=oseba.ime,
                    podatki_uporabnika=oseba.trenutni_portfelj(),
                    transakcije=oseba.transakcije(), 
                    rezultat=rezultat,
                    donosnost=oseba.donosnost(), 
                    stanje=oseba.stanje(), 
                    podatki_cas=datumi, 
                    podatki_vrednost=vrednosti,
                    minimum=0.9*spodnja_meja, 
                    maximum=1.1*zgornja_meja,
                    labels=labels,
                    vrednosti_tortni=values,
                    oznake=oznake,
                    barve=barve
                   )


@route('/odjava', method='POST')
def odjava():
    response.delete_cookie('user')
    return template('index_db_borza.html', rezultat='Odjava je uspela')


@route('/statistika', method='POST')
def statistika():
    datum = request.forms.get('datum')
    oseba_cookie = request.cookies.get('user')

    oseba = vlagatelj(oseba_cookie, None)

    return template('statistika.html',
                    podatki_cas=[],
                    podatki_vrednost=[],
                    minimum=0,
                    maximum=100,
                    naslov_grafa="Graf cen vrednostnega papirja")


@route('/poizvedba', method='POST')
def statistika():
    simbol = request.forms.get('simbol')
    natancnost = request.forms.get('natancnost')
    zacetek = request.forms.get('zacetek')
    konec = request.forms.get('konec')
    
    #datumi, vrednosti = pretvori_rezultat_v_seznama(dodaj_vrednosti(simbol))
    #casi, cene = ustvari_obdobje(zacetek, konec, datumi, vrednosti)
    #podatki_datumi, podatki_cene = doloci_frekvenco_podatkov(natancnost, casi, cene)
    ime_podjetja = IMENA_PODJETIJ.get(simbol, simbol)
    naslov_grafa = f" Cena podjeta {ime_podjetja} v obdobju {zacetek} - {konec}, {natancnost}"
    podatki_datumi, podatki_cene = opb_borza_model.poizvej_podatke(simbol, natancnost, zacetek, konec)
    spodnja_meja = min(podatki_cene)
    zgornja_meja = max(podatki_cene)
    return template('statistika.html', 
                    podatki_cas=podatki_datumi, 
                    podatki_vrednost=podatki_cene,
                    minimum=0.9*spodnja_meja, 
                    maximum=1.1*zgornja_meja, 
                    naslov_grafa=naslov_grafa)


@route('/portfelj', method='POST')
def portfelj():
    datum = request.forms.get('datum')
    oseba_cookie = request.cookies.get('user')
    rezultat = 'Dobrodošli nazaj na portfelj!'
    oseba = vlagatelj(oseba_cookie, None)

    datumi, vrednosti = opb_borza_model.portfelj_po_dnevih(oseba.ime)
    if not datumi or not vrednosti:
        datumi = []
        vrednosti = []
        spodnja_meja = 0
        zgornja_meja = 1
    else:
        spodnja_meja = min(vrednosti)
        zgornja_meja = max(vrednosti)
        struktura = opb_borza_model.struktura_portfelja(oseba.ime)
        skupna_vrednost = sum([float(r[3]) for r in struktura])
        labels = [IMENA_PODJETIJ.get(row[0], row[0]) for row in struktura]
        values = [round(float(row[3]), 2) for row in struktura]
        delezi = [round(100 * v / skupna_vrednost, 1) for v in values]
        oznake = [f"{label} ({d}%)" for label, d in zip(labels, delezi)]
        barve = [f"rgba({(i*47)%255}, {(i*83)%255}, {(i*61)%255}, 0.7)" for i in range(len(values))]

    return template('portfelj.html',
                    ime_uporabnika=oseba.ime,
                    podatki_uporabnika=oseba.trenutni_portfelj(),
                    transakcije=oseba.transakcije(),
                    rezultat=rezultat,
                    donosnost=oseba.donosnost(),
                    stanje=oseba.stanje(),
                    podatki_cas=datumi,
                    podatki_vrednost=vrednosti,
                    minimum=0.9 * spodnja_meja,
                    maximum=1.1 * zgornja_meja,
                    naslov_grafa=f"Portfelj uporabnika {oseba.ime}",
                    labels=labels,
                    vrednosti_tortni=values,
                    oznake=oznake,
                    barve=barve
                   )



run(host='localhost', port=8080, debug=True)
