CREATE TABLE Portfelj (
    ID SERIAL PRIMARY KEY,           -- Primarni ključ, samodejno se generira, vsaka vrednost mora biti edinstvena
    opis VARCHAR(1000),              -- Besedilni stolpec, omejen na 1000 znakov, lahko je prazen
    Datum_nastanka TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL -- Samodejno nastavi datum in čas vnosa, ne sme biti prazen
	Sredstva NUMERIC(10,2) DEFAULT 0 -- sredstva na voljo za kupovanje
	);



CREATE TABLE Uporabnik (
    ID SERIAL PRIMARY KEY,            -- Primarni ključ, samodejno se generira
    ime VARCHAR(50) NOT NULL,         -- Besedilni stolpec, omejen na 50 znakov, ne sme biti prazen
    ID_portfelja INT NOT NULL,        -- Številčni stolpec, ne sme biti prazen
	Sredstva NUMERIC(10,2) DEFAULT 10000, -- Začetna vsota sredstev, ki jih lahko razporedi med svoje portfelje
    CONSTRAINT fk_portfelj FOREIGN KEY (ID_portfelja) REFERENCES Portfelj(ID)  -- Zunanji ključ, ki se nanaša na 'ID' v tabeli 'Portfelj'
);


CREATE TABLE Vrednosti-papirjev(
	

);

CREATE TABLE Portfeljske-transakcije (
	ID SERIAL PRIMARY KEY UNIQUE,			-- PRimarni ključ, se samodejno generira
	ID_Portfelja INT NOT NULL,
	
	
);