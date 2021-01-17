import sqlite3

conn = sqlite3.connect('woningnet.db')
c = conn.cursor()

c.execute('''
CREATE TABLE publicatie (
    id integer primary key,
    adres text, 
    plaats text, 
    omschrijving text, 
    aanbieder text,
    prijs text, 
    kamers integer, 
    afbeelding text, 
    eind_datum timestamp,
    begin_datum timestamp, 
    datum_beschikbaar timestamp,
    latitude real,
    longitude real,
    publicatie_model text,
    woonwens integer,
    oppervlakte real,
    soort text,
    sociale_huur integer
);
''')

c.execute('''
CREATE TABLE status (
    publicatie integer,
    datum timestamp,
    reacties integer,
    positie integer
);
''')

conn.commit()

conn.close()
