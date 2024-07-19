CREATE TABLE Portfelj (
    ID SERIAL PRIMARY KEY,           -- Primarni ključ, samodejno se generira, vsaka vrednost mora biti edinstvena
    opis VARCHAR(1000) DEFAULT 'Brez opisa',              -- Besedilni stolpec, omejen na 1000 znakov, lahko je prazen
    Datum_nastanka TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL -- Samodejno nastavi datum in čas vnosa, ne sme biti prazen
	Sredstva NUMERIC(10,2) DEFAULT 0 NOT NULL -- sredstva na voljo za kupovanje
	);



CREATE TABLE Uporabnik (
    ID SERIAL PRIMARY KEY,            -- Primarni ključ, samodejno se generira
    ime VARCHAR(50) NOT NULL,         -- Besedilni stolpec, omejen na 50 znakov, ne sme biti prazen
    ID_portfelja INT NOT NULL,        -- Številčni stolpec, ne sme biti prazen
	Sredstva NUMERIC(10,2) DEFAULT 10000, -- Začetna vsota sredstev, ki jih lahko razporedi med svoje portfelje
    CONSTRAINT ID_Portfelja_od_uporabnika FOREIGN KEY (ID_portfelja) REFERENCES Portfelj(ID)  -- Zunanji ključ, ki se nanaša na 'ID' v tabeli 'Portfelj'
);


CREATE TABLE Vrednosti_od_papirjev(
	ID CHAR(4) PRIMARY KEY,             -- Primarni ključ za vrednostni papir za nek datum, sprejme kratico, ki jo uporablja borza
    ID_Papirja INT NOT NULL,           -- Zunanji ključ od papirja, tam se prebere osnovne podatke o vrednostnem papirju
    Datum DATE DEFAULT CURRENT_DATE NOT NULL    -- Datum vnosa vrednosti 
    Vrednost NUMERIC(10,2) NOT NULL    -- Pove vrednost delnice vrednostnega papirja na datum vnosa
    CONSTRAINT 
);

CREATE TABLE Portfeljske_transakcije (
	ID SERIAL PRIMARY KEY UNIQUE,			-- PRimarni ključ, se samodejno generira
	ID_Portfelja INT NOT NULL,
	
	
);

CREATE TABLE Vrednostni_papirji (
    ID SERIAL PRIMARY KEY,              -- Primarni ključ, ki bo u bistvu zaporedna številka nekega vrednostnega papirja
    Kratica CHAR(4) NOT NULL,           -- Kratica se bo uporabljala kot primarni ključ pri določanju vrste vrednostnega papirja
    Ime_papirja VARCHAR(30) NOT NULL,   -- POve polno ime vrednostnega papirja
    Datum_prvega_trgovanja DATE DEFAULT CURRENT_DATE NOT NULL ,   -- Datum orvega vnosa. Morda se kasneje pojavijo nove delnice, tako, da bo nekoč morda prišlo prav pri isaknju zgodovine, hitrejši queryji
    Opis VARCHAR(200)                   -- Morebitni opisi, opombe 
);