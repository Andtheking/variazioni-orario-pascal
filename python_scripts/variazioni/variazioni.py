import datetime
import hashlib
import os
import threading
import time
import bs4
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class DocenteAssente:
    def __init__(self, ora: int, classeAula: str, profAssente: str, sostituti: str, note: str):
        self.ora = ora # 1
        self.classeAula = classeAula # "4I(78)"
        self.profAssente = profAssente # "Nome C."
        self.sostituti = sostituti # "Nome C."
        self.note = note # "La classe entra alla 2° ora"

URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"

semaforo = threading.Semaphore()

sent_pdfs: dict[str,datetime.datetime] = {}

def ottieniLinkPdf(dataSelezionata: str) -> str: 
    """
    Ottieni il link del pdf dal sito del Pascal
    
    Args:
        dataSelezionata Data del giorno scelto in formato giorno-mese

    Return:
        (str) percorso pdf scaricato o errore
    """


    data = dataSelezionata.split('-')


    
    soup = BeautifulSoup(requests.get(URL).content, "html.parser").find_all("a")

    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]

    link = ""
    for linkPdf in listaPdf:
        if (f"-{data[0]}-" in linkPdf.lower() or f"-{data[0][1:]}-" in linkPdf.lower()) and f"{convertiMese(data[1]).lower()}" in linkPdf.lower():
            link = linkPdf
    if (link == ""):
        return None

    
    return link

def scaricaPdf(link: str) -> str:
    response = requests.get(link)
    
    with open(f'pdfScaricati/{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)
    
    return f'pdfScaricati/{link[link.rindex("/")+1:]}'

def convertiMese(n: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return mesi[int(n)-1].capitalize()

def CercaClasse(classe: str, docentiAssenti: list[DocenteAssente]) -> str:
    

    variazioniClasse = []

    for docente in docentiAssenti:
        if classe in docente.classeAula:
            variazioniClasse.append(docente)
    
    return variazioniClasse

REGEX_OUTPUT = r"^(?P<ora>[1-6])(?P<classe>[1-5][A-Z])\((?P<aula>.+?)\)(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"

def Main(classeDaCercare: str, giorno: str = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m"),onlyLink=False) -> str:
    #TODO Quando due utenti fanno un comando allo stesso tempo, non si deve bloccare


    giorno = formattaGiorno(giorno)
    
    if (onlyLink):
        l = ottieniLinkPdf(giorno)
        return l if l != None else f"Non è stata pubblicata una variazione orario per il `{giorno}`"

    
    # datetime.datetime.now() > csv[nomeCsv] + datetime.timedelta(minutes=10)
    
    semaforo.acquire()
    
    linkPdf = ottieniLinkPdf(giorno)

    if linkPdf == None:
        semaforo.release()
        return f"Non è stata pubblicata una variazione orario per il `{giorno}`"


    percorsoPdf = f'pdfScaricati/{linkPdf[linkPdf.rindex("/")+1:]}'
    
    # percorsoPdf = "pdfScaricati/Variazioni-orario-MERCOLEDI-24-GENNAIO-v4.pdf" # PER TEST
    
    semaforo.release()
    docentiAssenti = LeggiPdf(percorsoPdf)

    semaforo.release()

    variazioni = FormattaOutput(CercaClasse(classeDaCercare,docentiAssenti),giorno=giorno, classe=classeDaCercare)
    return variazioni

def LeggiPdf(percorsoPdf) -> list[DocenteAssente]:
    docentiAssenti: list[DocenteAssente] = []
    
    pdfReader = PyPDF2.PdfReader(percorsoPdf)

    pages = pdfReader.pages

    pdfTextPolished = ""
    for page in pages:
        pdfText = page.extract_text()
        sheesh = pdfText.split('\n')
        
        while len(sheesh[0]) != 3 or sheesh[0] == "Ora":
            del sheesh[0]

        for string in sheesh:
            if string != '':
                pdfTextPolished += string + '\n'
        pass
        
    pdfTextArray = pdfTextPolished.split('\n')
        
        
    for i in range(0,len(pdfTextArray)-1,2):
        test1 = pdfTextArray[i] + pdfTextArray[i+1]
        test2 = pdfTextArray[i-1] + pdfTextArray[i]
        
        try:
            informazioni = re.match(REGEX_OUTPUT,test1).groupdict()
        except:
            informazioni = re.match(REGEX_OUTPUT,test2).groupdict()

        for key, value in informazioni.items():
            informazioni[key] = value.strip() if value != None else value

        docentiAssenti.append(
            DocenteAssente(
                informazioni['ora'],
                informazioni['classe']+"("+informazioni['aula']+")",
                informazioni['prof_assente'],
                informazioni['sostituto_1'] + ' | ' + informazioni["sostituto_2"],
                informazioni["note"]
                )
            ) 
    
    return docentiAssenti

def FormattaOutput(variazioniOrario: list[DocenteAssente], giorno: str, classe: str):
    
    if variazioniOrario == None or variazioniOrario == []:
        return f"Nessuna variazione orario per la `{classe}` il `{giorno}`"
    
    stringa = ""

    for docente in variazioniOrario:
        stringa += (
f"""Ora: `{docente.ora}`
Classe(Aula): `{docente.classeAula}`
Docente assente: `{docente.profAssente}`
Sostituito da: `{docente.sostituti.replace(' | ', ' e ')}`
Note: `{docente.note}`\n\n"""
                        )

    
    return f"Variazioni orario della `{classe}` per il `{giorno}`\n\n{stringa}"


# TODO: Da riguardare
def controllaVariazioniAule(classe: str,giorno: str):
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")

    giorno = formattaGiorno(giorno)
    giorno = giorno.split('-')
    daCercare = f"{giorno[0]} {convertiMese(giorno[1]).lower()}"

    lista: list[bs4.Tag]= soup.find("div", attrs={"class":"entry-content"}).findAll()
    trovato: int = None
    listaVariazioniAuleGiorno = []

    for i in range(len(lista)):
        i: bs4.Tag
        if lista[i].name == 'span':
            if (daCercare in lista[i].text):
                trovato = i

            elif (trovato != None):
                while  trovato < i-1:
                    if (lista[trovato].name == 'p'):
                        listaVariazioniAuleGiorno.append(lista[trovato].text)
                    trovato += 1
                trovato = None

    daReturnare: str = ''
    for i in listaVariazioniAuleGiorno:
        if classe in i:
            daReturnare+=i+"\n"

    if daReturnare != '':
        daReturnare = f'Variazioni aule per il `{giorno[0] + "-" + giorno[1]}`\n'+daReturnare

    return daReturnare

def formattaGiorno(giorno):
    
    if giorno == "domani" or giorno == "":
        giorno = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m")
    elif giorno == "oggi":
        giorno = datetime.datetime.now().strftime("%d-%m")


    giorno = giorno.replace("/","-")
    giorno = ('0' + giorno.split('-')[0] if not len(giorno.split('-')[0]) == 2 else giorno.split('-')[0]) + '-' + ('0' + giorno.split('-')[1] if not len(giorno.split('-')[1]) == 2 else giorno.split('-')[1])
    return giorno

def CancellaCartellaPdf():
    filelist = [ f for f in os.listdir("pdfScaricati/")]
    for f in filelist:
        os.remove(os.path.join("pdfScaricati/", f))

if __name__ == "__main__":
    #print(Main("4I"))
    print(Main("4I","24-01"))

    

