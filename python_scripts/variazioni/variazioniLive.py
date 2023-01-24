import requests
from bs4 import BeautifulSoup
from numpy import * 
import time
import hashlib
import python_scripts.variazioni.variazioni as variazioni
from telegram import Bot
from threading import Thread


URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"
TOKEN = "5744550511:AAHECgzzDotFxJgH_G3XwN7yfrXKmmhjFx4"

sent_pdfs: list[str]

try: 
    with open("sent_pdfs.txt","r") as f:
        sent_pdfs = f.readline().split(' - ')[0:-1]
except:
    open("sent_pdfs.txt","w").close()
    sent_pdfs = []

lastcheck = [""]

def get_pdf_hash(filepath):
    """
    Calcola l'hash del contenuto del pdf
    """
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as pdf:
        buf = pdf.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = pdf.read(BLOCKSIZE)
    return hasher.hexdigest()

def ottieni_info(utenti: list[list[str]], bot: Bot, soup = None): # Viene invocato se la pagina risulta essere stata cambiata
    if (soup == None):
        Ok = False
        while not Ok:
            try:
                response = requests.get(URL)
                soup = BeautifulSoup(response.text, 'html.parser')
                Ok = True
            except:
                Ok = False

        
    
    links = soup.find_all('a')
    i = 0

    for link in links: # Controlla tutti i link nella pagina
        if ('.pdf' in link.get('href', [])): # Se è un pdf lo scarica
            i += 1
            print("Downloading file: ", i)
            
            # Get response object for link
            Ok = False
            while not Ok:
                try:
                    response = requests.get(link.get('href'))
                    Ok = True
                except:
                    Ok = False
                
            pdfName = "pdfScaricati/" + response.url[response.url.rindex("/")+1:]
            giorno = GetGiorno(response.url)
            
            # Write content in pdf file
            pdf = open(pdfName, 'wb')
            pdf.write(response.content) # scarica il contenuto del pdf in un file
            pdf.close()

            pdf_hash = get_pdf_hash(pdfName)
            
            global sent_pdfs
            
            if pdf_hash in sent_pdfs: # se il pdf e gia stato inviato non lo invia di nuovo
                continue
            
            sent_pdfs.append(pdf_hash)           

            with open("sent_pdfs.txt","w") as f:
                for ki in sent_pdfs:
                    f.write(ki + ' - ')

            for utente in utenti:
                classe = utente[2]
                id = utente[0]

                variazioniOrario = variazioni.LeggiPdf(pdfName)
                variazioniOrarioClasse = variazioni.CercaClasse(classe,variazioniOrario)
                stringa = variazioni.FormattaOutput(variazioniOrarioClasse,giorno=giorno,classe=classe)
                
                try:
                    bot.send_message(chat_id=id, text=stringa, parse_mode="Markdown")            
                    print(f"Mandate variazioni {classe} a {utente[1]}")
                except:
                    pass

ID_TELEGRAM_AND = "245996916"

def GetGiorno(url: str):
    url = url[url.rindex('/')+1:]
    test = url.split('-')
    del test[0:3]
    giorno = test[0] + "-" + convertiMese(test[1].lower())
    return giorno

def convertiMese(mese: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    for i,m in enumerate(mesi):
        if mese == m:
            i+=1
            return str(i) if i > 9 else '0' + str(i)