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
        self.ora = ora  # 1
        self.classeAula = classeAula  # "4I(78)"
        self.profAssente = profAssente  # "Nome C."
        self.sostituti = sostituti  # "Nome C."
        self.note = note  # "La classe entra alla 2° ora"


URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"

semaforo = threading.Semaphore()

sent_pdfs: dict[str, datetime.datetime] = {}


def ottieniLinkPdf(dataSelezionata: str) -> str:
    """
    Ottieni il link del pdf dal sito del Pascal
    
    Args:
        dataSelezionata Data del giorno scelto in formato giorno-mese

    Return:
        (str) percorso pdf scaricato o errore
    """

    data = dataSelezionata.split('-')

    soup = BeautifulSoup(requests.get(URL).content,
                         "html.parser").find_all("a")

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
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return mesi[int(n)-1].capitalize()

def CercaClasse(classe: str, docentiAssenti: list[DocenteAssente]) -> list[DocenteAssente]:

    variazioniClasse = []

    for docente in docentiAssenti:
        if classe in docente.classeAula:
            variazioniClasse.append(docente)

    return variazioniClasse

def CercaSostituto(sostituto: str, docentiAssenti: list[DocenteAssente]) -> list[DocenteAssente]:

    variazioniClasse = []

    for docente in docentiAssenti:
        if sostituto in docente.sostituti:
            variazioniClasse.append(docente)

    return variazioniClasse

REGEX_OUTPUT = r"^(?P<ora>[1-6])(?P<classe>[1-5][A-Z])\((?P<aula>.+?)\)(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"


def Main(daCercare: str, giorno: str = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m"), onlyLink=False, prof=False) -> str:
    giorno = formattaGiorno(giorno)

    if (onlyLink):
        l = ottieniLinkPdf(giorno)
        return l if l != None else f"Non è stata pubblicata una variazione orario per il `{giorno}`"

    linkPdf = ottieniLinkPdf(giorno)

    if linkPdf == None:
        return f"Non è stata pubblicata una variazione orario per il `{giorno}`"

    percorsoPdf = f'pdfScaricati/{linkPdf[linkPdf.rindex("/")+1:]}'

    semaforo.acquire()
    try:
        docentiAssenti = LeggiPdf(percorsoPdf)
    except:
        semaforo.release()
        return f"Qualcosa è andato storto nella lettura del pdf del giorno `{giorno}`.\n\nEcco il link:\n{linkPdf}"
    semaforo.release()
    
    if (not prof):
        variazioni = FormattaOutput(
            CercaClasse(
                daCercare, docentiAssenti
            ), 
            giorno=giorno, 
            classeOProf=daCercare
            )
    else:
        daCercare = daCercare.title()
        variazioni = FormattaOutput(
            CercaSostituto(
                sostituto=daCercare,
                docentiAssenti=docentiAssenti
            ),
            giorno=giorno,
            classeOProf=daCercare
        )
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

    for i in range(0, len(pdfTextArray)-1, 2):
        test1 = pdfTextArray[i] + pdfTextArray[i+1]
        test2 = pdfTextArray[i-1] + pdfTextArray[i]

        try:
            informazioni = re.match(REGEX_OUTPUT, test1).groupdict()
        except:
            informazioni = re.match(REGEX_OUTPUT, test2).groupdict()

        for key, value in informazioni.items():
            informazioni[key] = value.strip() if value != None else value

        docentiAssenti.append(
            DocenteAssente(
                informazioni['ora'],
                informazioni['classe']+"("+informazioni['aula']+")",
                informazioni['prof_assente'],
                informazioni['sostituto_1'] + ' | ' +
                informazioni["sostituto_2"],
                informazioni["note"]
            )
        )

    return docentiAssenti


def FormattaOutput(variazioniOrario: list[DocenteAssente], giorno: str, classeOProf: str):
    prof = False
    if len(classeOProf) != 2:
        prof = True

    if variazioniOrario == None or variazioniOrario == []:
        return f"Nessuna variazione orario per {'la' if not prof else 'il/la prof'} `{classeOProf}` il `{giorno}`"

    stringa = ""

    for docente in variazioniOrario:
        stringa += (
            f"""Ora: `{docente.ora}`
Classe(Aula): `{docente.classeAula}`
Docente assente: `{docente.profAssente}`
Sostituito da: `{docente.sostituti.replace(' | ', ' e ')}`
Note: `{docente.note}`\n\n"""
        )

    return f"Variazioni orario per {'la' if not prof else 'il/la prof'} `{classeOProf}` per il `{giorno}`\n\n{stringa}"


def controllaVariazioniAuleClasse(classe: str, giorno: str, lista = None):
    giorno = formattaGiorno(giorno)
    giorno = giorno.split('-')
    daCercare = f"{giorno[0]} {convertiMese(giorno[1]).lower()}"
    
    if lista is None:
        lista = leggiTutteVariazioniAule()
    # print(lista)

    sheesh: list[bs4.Tag] = []
    for item in lista:
        temp = daCercare in item.text or ((' '+ daCercare[1:]) if daCercare[0] == '0' else daCercare) in item.text
        if temp:
            sheesh = list(item.next_elements)

    test2 = []
    for a in sheesh:
        test2.append(a)
        if a.name == 'span' and (("ff0000" in a.attrs['style']) if 'style' in a.attrs else False):
            break

    test3 = []

    for b in test2:

        if '' in b:
            test3.append(b)

    stringaEnorme = ""
    for a in test3:
        stringaEnorme += a

    stringaEnormeSplit = stringaEnorme.split('\n')

    daReturnare: str = ""
    
    for i in stringaEnormeSplit:
        if classe in i:
            daReturnare += i + '\n'

    daReturnare = daReturnare[0:-1]

    if daReturnare != '':
        daReturnare = f'Variazioni aule per il `{giorno[0] + "-" + giorno[1]}`\n\n'+daReturnare[0].upper() + daReturnare[1:] + ('.' if daReturnare[-1] != '.' else '')

    return daReturnare.replace(r"\xa","")

def leggiTutteVariazioniAule():
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")
    lista: list[bs4.Tag] = soup.select(
        "p > span", attrs={"style": "color: #ff0000"})
        
    return lista

def formattaGiorno(giorno):

    if giorno == "domani" or giorno == "":
        giorno = (datetime.datetime.now() +
                  datetime.timedelta(days=1)).strftime("%d-%m")
    elif giorno == "oggi":
        giorno = datetime.datetime.now().strftime("%d-%m")

    giorno = giorno.replace("/", "-")
    giorno = ('0' + giorno.split('-')[0] if not len(giorno.split('-')[0]) == 2 else giorno.split('-')[
              0]) + '-' + ('0' + giorno.split('-')[1] if not len(giorno.split('-')[1]) == 2 else giorno.split('-')[1])
    return giorno
        
def CancellaCartellaPdf():
    filelist = [f for f in os.listdir("pdfScaricati/")]
    for f in filelist:
        os.remove(os.path.join("pdfScaricati/", f))

if __name__ == "__main__":
    #print(Main("4I"))
    Main
    while True:
        print(controllaVariazioniAuleClasse(input("Classe -> "), input("Data (31-12) -> ")))
