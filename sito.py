from logging import exception
import string
import requests, pandas as pd
import os, datetime
import logging

URL = 'http://www.sostituzionidocenti.com/fe/controllaCodice.php/'

PAYLOAD = {
        'pass': 'PC88075LD'
    }


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def GetUrl():
    with requests.Session() as s:
        
        p = s.post(URL, data=PAYLOAD)

        r = s.get('http://www.sostituzionidocenti.com/fe/sostituzioni.php?offset=0')    
        
        oggi = datetime.date.today().strftime('%A')
        
        if oggi != "Sunday":
            f = open('html.html', 'w')
            f.write(r.text)
            f.close()
            logger.info('HTML stampato su file html.html con successo')
        else:
            logger.info('Oggi è Domenica, non ci sono variazioni.')

def Main(classeToFind):

    stringa = ''
    
    GetUrl()
        
    tabella = pd.read_html('html.html', match='Classe')
    df = tabella[0]
    df.head()

    docente = []
    ore = []
    note = []
    classe = []
    sostituto = []

    k = 0
    
    
    for i in range(len(df['Classe'])):
        if classeToFind in df['Classe'][i]:
            
            docente.append(df['Doc.Assente'][i])
            ore.append(df['Ora'][i])
            note.append(df['Note'][i])
            classe.append(df['Classe'][i])
            sostituto.append(df['Sost.1'][i])

            k += 1
        if i == len(df['Classe'])-1 and k == 0:
            stringa = f"Nessuna variazione orario per la {classeToFind}."
    
    l = 0
    
    while (l < k):
        if l < len(docente)-1:
            if docente[l] == docente[l+1]:
                stringa += f"Ore: {ore[l]} e {ore[l+1]}\nClasse(Aula): {classe[l]}\nDocente assente: {docente[l]}\nSostituito da: {sostituto[l]}\nNote: {note[l]}\n\n"
                l += 2
            else:
                stringa += f"Ora: {ore[l]}\nClasse(Aula): {classe[l]}\nDocente assente: {docente[l]}\nSostituito da: {sostituto[l]}\nNote: {note[l]}\n\n" 
                l += 1
        else:
            stringa += f"Ora: {ore[l]}\nClasse(Aula): {classe[l]}\nDocente assente: {docente[l]}\nSostituito da: {sostituto[l]}\nNote: {note[l]}\n\n" 
            l += 1

    return stringa