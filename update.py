import math
import json
import sqlite3
from datetime import datetime
from base64 import b64decode
import requests
from bs4 import BeautifulSoup

baseurl = 'https://www.woningnetregioamsterdam.nl'
s = requests.Session() 

# Get initial cookies and form token needed to log in.
r = s.get(f'{baseurl}/Inloggen')
soup = BeautifulSoup(r.text, 'html.parser')
token = list(soup.find(id='inloggenForm').children)[0]['value']

# Log in.
with open('info.json', 'r') as f:
    info = json.load(f)

data = {}
data['gebruikersnaam'] = b64decode(info['n']).decode('utf-8')
data['password'] = b64decode(info['w']).decode('utf-8')
data['__RequestVerificationToken'] = token
data['ReturnUrl'] = ''
data['OnthoudGebruikersnaam'] = 'false'

r = s.post(f'{baseurl}/Inloggen', data)
r.status_code

#
conn = sqlite3.connect('woningnet.db')
c = conn.cursor()

# Update nieuwe publicaties.
n_per_page = 10
page = 1
ids = []

while True:
    r = s.post(f'{baseurl}/webapi/zoeken/find', 
               {'command': f'page[{page}]'})
    j = r.json()

    # 
    for publicatie in j['Resultaten']:
        pub_id = int(publicatie['PublicatieId'])
        ids.append(pub_id)

        c.execute('SELECT * FROM publicatie WHERE id = ?', (pub_id,))
        entry = c.fetchone()

        if entry is not None:
            continue

        values = [
            pub_id,
            publicatie['Adres'],
            publicatie['PlaatsWijk'],
            publicatie['Omschrijving'],
            publicatie['Aanbieder'],
            publicatie['Prijs'],
            None if publicatie['Kamers'] == '' else int(publicatie['Kamers']),
            publicatie['AfbeeldingUrl'],
            datetime.fromisoformat(publicatie['PublicatieEinddatum']),
            datetime.fromisoformat(publicatie['PublicatieBegindatum']),
            datetime.strptime(publicatie['PublicatieBeschikbaarPer'], '%d-%m-%Y %H:%M:%S'),
            publicatie['Latitude'],
            publicatie['Longitude'],
            publicatie['PublicatieModel'],
            int(publicatie['IsWoonwensMatch']),
            # float(publicatie['Woonoppervlakte']),
            None if publicatie['Woonoppervlakte'] == '' else float(publicatie['Woonoppervlakte']),
            publicatie['DetailSoortOmschrijving'],
            int(publicatie['IsSocialeHuur'])
        ]
        c.execute('''
        INSERT INTO publicatie VALUES (?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', values)
        conn.commit()

    # Check if we hit last page
    n_results = j['TotalSearchResults']
    n_pages = math.ceil(n_results / n_per_page)
    if page == n_pages:
        break
    page += 1

# Update positie en reacties voor publicaties.
nu = datetime.now()

for pos in range(0, len(ids), n_per_page):
    ids_sub = ids[pos:pos + n_per_page]
    ids_sub_str = ','.join([str(x) for x in ids_sub])
    r = s.get(f'{baseurl}/webapi/publicatie/GetPositieEnReacties/{ids_sub_str}')
    j = r.json()
    for publicatie in j:
        values = [
            int(publicatie['PublicatieId']),
            nu,
            int(publicatie['AantalReacties']),
            int(publicatie['VoorlopigePositie'])
        ]
        c.execute('''
        INSERT INTO status VALUES (?, ?, ?, ?);
        ''', values)
        conn.commit()

conn.close()
