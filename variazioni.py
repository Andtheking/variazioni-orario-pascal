import datetime
import math
import os
import threading

import bs4
import pandas as pd
import PyPDF2
import requests
from bs4 import BeautifulSoup
from tabula import convert_into


class DocenteAssente:
    def __init__(self, ora: int, classeAula: str, profAssente: str, sostituti: str, note: str):
        self.ora = ora # 1
        self.classeAula = classeAula # "4I(78)"
        self.profAssente = profAssente # "Nome C."
        self.sostituti = sostituti # "Nome C."
        self.note = note # "La classe entra alla 2° ora"

class Csv:
    def __init__(self, formato: int):
        self.data = datetime.datetime.now()
        self.formato: int = formato

URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"

semaforo = threading.Semaphore()

# pdf: dict[datetime.datetime] = {}


csv: dict[str,Csv] = {} # Per tenere conto del tempo di ogni csv



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
        raise Exception(f"Non è stata pubblicata una variazione orario per il `{dataSelezionata}`")

    return link

def scaricaPdf(link: str) -> str:
    response = requests.get(link)
    
    with open(f'pdfScaricati/{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)
    
    return f'pdfScaricati/{link[link.rindex("/")+1:]}'

def pdfToCsv(percorsoPdf: str, nomeOutput: str, gradi: int, lattice:bool) -> str:
    print("Entrato in pdfToCsv")
    nomeCsv = f"{nomeOutput}.csv"
    percorsoCsv = f"pdfScaricati/{nomeCsv}"

    # global csv
    # if ((nomeCsv in list(csv.keys())) and (not datetime.datetime.now() > csv[nomeCsv] + datetime.timedelta(minutes=10))):
    #     return percorsoCsv

    # if nomeCsv in list(csv.keys()):
    #     csv.pop(nomeCsv)

    ruotaPdf(percorsoPdf, gradi)
    print("Ruotato")
    percorsoPdf = percorsoPdf[0:percorsoPdf.rindex("/")+1] + f"{gradi}" + percorsoPdf[percorsoPdf.rindex("/")+1:]
    
    convert_into(percorsoPdf, percorsoCsv, pages="all", lattice=lattice)
    print("Convertito")

    return percorsoCsv
    
def convertiMese(n: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return mesi[int(n)-1].capitalize()

# Risolvo il problema delle virgole (Se c'erano virgole in più nel csv)
def clean_up(csv_file: str):
    cambi = 0
    numeroVirgole = 0
    rename = csv_file[0:csv_file.rindex("/")] + "/-" + csv_file[csv_file.rindex("/")+1:]
    
    with open(csv_file,"r") as f:
        for riga in f:
            if numeroVirgole < len(riga.split(",")):
                numeroVirgole = len(riga.split(","))
                cambi += 1
    
    if cambi > 1:
        with open(csv_file,"r") as f:
            with open(rename,"w") as f2:
                for riga in f:
                    roba = riga.rstrip('\n') + "," * (numeroVirgole-len(riga.split(","))) + "\n"
                    f2.write(roba) 

    if (os.path.exists(rename)):
        os.remove(csv_file)
        os.rename(rename,csv_file)
    
    return csv_file

# Rigorosamente copia-incollato da internet
# Sauce: https://www.johndcook.com/blog/2015/05/01/rotating-pdf-pages-with-python/
def ruotaPdf(percorsoPdf: str, gradi: int):
    try:

        percorsoPdfRuotato = percorsoPdf[0:percorsoPdf.rindex("/")+1] + f"{gradi}" + percorsoPdf[percorsoPdf.rindex("/")+1:]

        pdf_in = open(percorsoPdf, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_in)
        pdf_writer = PyPDF2.PdfFileWriter()

        for pagenum in range(pdf_reader.numPages):
            page = pdf_reader.getPage(pagenum)
            page.rotateClockwise(gradi)
            pdf_writer.addPage(page)

        pdf_out = open(percorsoPdfRuotato, 'wb')
        pdf_writer.write(pdf_out)
        pdf_out.close()
        pdf_in.close()
    
	# pdf[percorsoPdfRuotato] = datetime.datetime.now()
    except Exception as ex:
            print(str(ex))

def pdfFormato2(docentiAssenti: list[DocenteAssente], asd: pd.DataFrame):
    i = 0
    while i < len(asd.values):
        if (i+1 < len(asd.values) and math.isnan(asd.values[i+1][1])):
            i+=1
            continue
        if (i+1 < len(asd.values)):
            ora = int(asd.values[i+1][1])   
            classeAula = asd.values[i][2]+asd.values[i+2][2]
            robo = 0
            if type(asd.values[i+1][3]) == type(1.0):
                robo = 1
                    
            profAssente = asd.values[i+1][3+robo]
            supplenti = asd.values[i+1][4+robo] + " | " + asd.values[i+1][5+robo]
            note = asd.values[i+1][7+robo] if not type(asd.values[i+1][7+robo]) == type(1.0) else "Nessuna"

            docentiAssenti.append(DocenteAssente(ora,classeAula,profAssente,supplenti,note))
            i+=3

def pdfFormato1(docentiAssenti: list[DocenteAssente], asd: pd.DataFrame, daRimuovere):
    for riga in asd.values:
        riga: str

        if (riga[0] == daRimuovere):
            continue

        docentiAssenti.append(DocenteAssente(int(riga[0]),riga[1].replace("\r",""),riga[2],riga[3] + " | " + riga[4],riga[6]))

def CercaClasse(classe: str, docentiAssenti: list[DocenteAssente], giorno: str):
    stringa = ""
    
    i = 0
    try:
        while i < len(docentiAssenti):
            if classe in docentiAssenti[i].classeAula:
                stringa += f"Ora: `{docentiAssenti[i].ora}`\nClasse(Aula): `{docentiAssenti[i].classeAula}`\nDocente assente: `{docentiAssenti[i].profAssente}`\nSostituito da: `{docentiAssenti[i].sostituti.replace(' | ', ' e ')}`\nNote: `{docentiAssenti[i].note}`\n\n" 
            i += 1

        if stringa == "":
            return f"Nessuna variazione orario per la `{classe}` il `{giorno}`"
        else:
            return f"Variazioni orario della `{classe}` per il `{giorno}`\n\n{stringa}"
    except Exception as e:
        print(str(e))
        return f"C'è stato un problema col pdf, ti mando il link diretto al download\n\n{ottieniLinkPdf(giorno)}"
    
def leggiCsv(percorsoCsv:str,giorno: str, formato: int) -> list[DocenteAssente] | None:
    
    
    docentiAssenti: list[DocenteAssente] = []
    
    try:
        asd = pd.read_csv(clean_up(percorsoCsv))
    except:
        raise Exception()


    if formato==1:
        pdfFormato1(docentiAssenti, asd, asd.columns[0])
    
    elif formato==2:
        pdfFormato2(docentiAssenti, asd)


    return docentiAssenti


def Main(classeDaCercare: str, giorno: str = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m"),onlyLink=False) -> str:
    #TODO Quando due utenti fanno un comando allo stesso tempo, non si deve bloccare


    giorno = formattaGiorno(giorno)
    
    if (onlyLink):
        try:
            return ottieniLinkPdf(giorno)
        except Exception as e:
            return str(e)

    
     # datetime.datetime.now() > csv[nomeCsv] + datetime.timedelta(minutes=10)
    global csv

    # Questo potrebbe essere la ragione della lentezza del bot
    semaforo.acquire()
    condizione2 = f"{giorno}.csv" in list(csv.keys())
    if condizione2:
        condizione3 = datetime.datetime.now() > csv[f"{giorno}.csv"].data + datetime.timedelta(minutes=10)

    if not condizione2 or condizione3:
        print("Scarico il pdf")
        try:
            percorsoPdf = scaricaPdf(ottieniLinkPdf(giorno))
            print("Scaricato")
        except Exception as e:
            semaforo.release()
            return str(e)
        try:
            print("Lo ruoto 1")
            pdf_Csv = pdfToCsv(percorsoPdf,giorno,90,True)
            print("Lo leggo")
            docentiAssenti = leggiCsv(pdf_Csv,giorno,1)
            csv[f"{giorno}.csv"] = Csv(1)
        except:
            try:
                print("Lettura fallita, riprovo con l'altro formato")
                pdf_Csv = pdfToCsv(percorsoPdf,giorno,270,False)
                print("Ruotato 2")
                docentiAssenti = leggiCsv(pdf_Csv,giorno,2)
                print("Letto")
                csv[f"{giorno}.csv"] = Csv(2)
            except:
                semaforo.release()
                return f"C'è stato un problema col pdf, ti mando il link diretto al download\n\n{ottieniLinkPdf(giorno)}"
    else:
        print("Non scarico il pdf")
        docentiAssenti = leggiCsv(f"pdfScaricati/{giorno}.csv",giorno, csv[f"{giorno}.csv"].formato)
    
    semaforo.release()

    if type(docentiAssenti) == type(""):
        return docentiAssenti
    
    return CercaClasse(classeDaCercare, docentiAssenti, giorno)


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
    variazioniOrario = Main('4I','domani')
    variazioniAule = controllaVariazioniAule('4I','domani')

    print(variazioniOrario + variazioniAule)

    

