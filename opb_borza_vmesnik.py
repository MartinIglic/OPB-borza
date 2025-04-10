from bottle import route, run, static_file, template, request, response, redirect
from opb_borza_model import vlagatelj
from opb_borza_model import *
import opb_borza_model
import psycopg2

# Database connection details
connection = psycopg2.connect(
    user='rokl',
    password='skn6t66w',
    host='baza.fmf.uni-lj.si',
    #port='8080',
    database='sem2024_rokl'
)


@route('/nov_uporabnik', method='POST')
def nov_uporabnik():
    uporabnik = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')
    rezultat = ''

    if uporabnik == '' or geslo == '':
        rezultat = 'Za kreiranje novega računa obvezno vnesite uporabniško ime in geslo.'
    else:
        try:
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM uporabnik WHERE ime = %s", (uporabnik,))
                existing_user = cursor.fetchone()

            if existing_user is None:
                
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO uporabnik (ime, geslo) VALUES (%s, %s)",
                        (uporabnik, geslo)
                    )
                    connection.commit()

                
                oseba = vlagatelj(uporabnik, geslo)
                main(danasnji_dan())    
                response.set_cookie('user', uporabnik)
                return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
                            transakcije=oseba.transakcije(), rezultat='Uporabnik uspešno kreiran.',
                            donosnost=oseba.donosnost(), stanje=oseba.stanje())

            else:
                rezultat = 'Uporabnik s tem uporabniškim imenom že obstaja. Vnesite drugo ime.'

        except Exception as e:
            rezultat = f'Prišlo je do napake: {str(e)}'

    return template('index_db_borza.html', rezultat=rezultat)


@route('/logiranje', method='POST')
def logiranje():
    uporabnik = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM uporabnik WHERE ime = %s AND geslo = %s", (uporabnik, geslo))
            existing_user = cursor.fetchone()
        if existing_user is None:
            return template('index_db_borza.html', rezultat='Uporabnik s tem uporabniškim imenom in geslom ne obstaja.')
        else:
            response.set_cookie('user', uporabnik)
            oseba = vlagatelj(uporabnik, geslo)
            main(danasnji_dan())    
            return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
                            transakcije=oseba.transakcije(), rezultat='',
                            donosnost=oseba.donosnost(), stanje=oseba.stanje())


    except Exception as e:
            rezultat = f'Prišlo je do napake: {str(e)}'
    
    return template('index_db_borza.html', rezultat=rezultat)



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
            
    return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
                            transakcije=oseba.transakcije(), rezultat=rezultat,
                            donosnost=oseba.donosnost(), stanje=oseba.stanje())



@route('/odjava', method='POST')
def odjava():
    response.delete_cookie('user')
    return template('index_db_borza.html', rezultat='Odjava je uspela')


@route('/statistika', method='POST')
def statistika():
    datum = request.forms.get('datum')
    oseba_cookie = request.cookies.get('user')

    oseba = vlagatelj(oseba_cookie, None)

    return template('statistika.html')

@route('/poizvedba', method='POST')
def statistika():
    simbol = request.forms.get('simbol')
    natancnost = request.forms.get('natancnost')
    zacetek = request.forms.get('zacetek')
    konec = request.forms.get('konec')
    datumi, vrednosti = pretvori_rezultat_v_seznama(dodaj_vrednosti(simbol))
    casi, cene = ustvari_obdobje(zacetek, konec, datumi, vrednosti)
    podatki_datumi, podatki_cene = doloci_frekvenco_podatkov(natancnost, casi, cene)
    spodnja_meja = min(podatki_cene)
    zgornja_meja = max(podatki_cene)
    return template('statistika.html', podatki_cas=podatki_datumi, podatki_vrednost=podatki_cene,
                    minimum=0.9*spodnja_meja, maksimum=1.1*zgornja_meja)


@route('/portfelj', method='POST')
def portfelj():
    datum = request.forms.get('datum')
    oseba_cookie = request.cookies.get('user')
    rezultat = 'Dobrodošli nazaj na portfelj!'
    oseba = vlagatelj(oseba_cookie, None)
    return template('portfelj.html', ime_uporabnika=oseba.ime, podatki_uporabnika=oseba.trenutni_portfelj(),
                            transakcije=oseba.transakcije(), rezultat=rezultat,
                            donosnost=oseba.donosnost(), stanje=oseba.stanje())



run(host='localhost', port=8080, debug=True)
