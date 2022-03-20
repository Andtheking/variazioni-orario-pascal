from logging import exception
import string
import requests, pandas as pd
import os

def Main(classeToFind):
    # Fill in your details here to be posted to the login form.
    classeToFind = classeToFind.replace('/impostaClasse', '')
    classeToFind = classeToFind.strip()
    
    if len(classeToFind) != 2:
        return "Non hai inserito una classe"
    try:
        if int(classeToFind[0:1]) < 0 and int(classeToFind[0:1]) > 5:
            return "Non hai inserito una classe"
    except Exception as ex:
        print(ex)
        return "Non hai inserito una classe"

    payload = {
        'pass': 'PC88075LD'
    }

    url = 'http://www.sostituzionidocenti.com/fe/controllaCodice.php/'

    # Use 'with' to ensure the session context is closed after use.
    with requests.Session() as s:
        p = s.post(url, data=payload)
        
        #print (p.text)

        r = s.get('http://www.sostituzionidocenti.com/fe/sostituzioni.php?offset=0')
        
        f = open('html.html', 'w')
        f.write(r.text)
        f.close()

        tabella=pd.read_html('html.html', match='Classe')
        df = tabella[0]
        df.head()

        docente = []
        k = 0
        

        # Da fare: Se una docente è assente per più ore --> Non stampa due volte tutto ma separa le ore con una virgola
        # Da fare: Output con il bot di telegram in bot.py
        docente = [None, None, None, None]
        ore = [None, None, None, None]
        note = [None, None, None, None]
        classe = [None, None, None, None]
        stringa = 'Qualcosa non va'
        k = 0
        
        for i in range(len(df['Classe'])):
            if classeToFind in df['Classe'][i]:
                
                docente[k] = df['Doc.Assente'][i]
                ore[k] = df['Ora'][i]
                note[k] = df['Note'][i]
                classe[k] = df['Classe'][i]

                k = k + 1
            if i == len(df['Classe'])-1 and k == 0:
                stringa = f"Nessuna variazione orario per la {classeToFind}."
        
        for l in range (k):
            if l == 0:
                if docente[l] == docente[l+1]:
                    stringa = f"Ore: {ore[l]} e {ore[l+1]}\nClasse(Aula): {classe[l]}\nDocente assente: {docente[l]}\nNote: {note[l]}"
                else:
                    stringa = f"Ora: {ore[l]}\nClasse(Aula): {classe[l]}\nDocente assente: {docente[l]}\nNote: {note[l]}" 

    print (stringa)
    return stringa
