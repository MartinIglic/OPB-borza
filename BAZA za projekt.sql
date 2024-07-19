CREATE TABLE Vlagatelj (
    ID SERIAL PRIMARY KEY,
    Ime VARCHAR(100) NOT NULL,
    Portfolio_ID INT
);



CREATE TABLE Portfelj (
    ID INT PRIMARY KEY,
    Opis VARCHAR(100) NOT NULL,
    Datum_nastanka DATE
);

CREATE TABLE Cena_papirjev (
    ID VARCHAR(5) PRIMARY KEY,
    Datum_vrednosti DATE,
	Vrednost INT
);

CREATE TABLE Portfeljske_transakcije (
    ID SERIAL PRIMARY KEY,
    Datum_transakcije DATE,
	Portfelj_ID INT,
	Papir_ID VARCHAR(5),
	kolicina INT,
	Opis VARCHAR(1000)
);
