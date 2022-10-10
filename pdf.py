from tabula import convert_into
import requests, pandas as pd
from bs4 import BeautifulSoup
import PyPDF2
import os
import datetime
import math
import threading


class DocenteAssente:
    def __init__(self, ora: int, classeAula: str, profAssente: str, sostituti: str, note: str):
        self.ora = ora # 1
        self.classeAula = classeAula # "4I(78)"
        self.profAssente = profAssente # "Nome C."
        self.sostituti = sostituti # "Nome C."
        self.note = note # "La classe entra alla 2° ora"

url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"
link: str
semaforo = threading.Semaphore()

ultimaVoltaScaricato = 0
tentativoDownload = 9999

def scaricaPdf(dataSelezionata: str, onlyLink: bool = False) -> str: 
    """
    Scarica il pdf dal sito del Pascal
    
    Args:
        dataSelezionata Data del giorno scelto in formato giorno-mese

    Return:
        (str) percorso pdf scaricato o errore
    """

    data = dataSelezionata.replace("/","-").split('-')

    soup = BeautifulSoup(requests.get(url).content, "html.parser").find_all("a")

    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]

    global link
    link = ""
    for linkPdf in listaPdf:
        #print(f"-{data[0]}- in {linkPdf.lower()} and {convertiMese(data[1]).lower()} in {linkPdf.lower()}")
        if (f"-{data[0]}-" in linkPdf.lower() or f"-{data[0][1:]}-" in linkPdf.lower()) and f"{convertiMese(data[1]).lower()}" in linkPdf.lower():
            link = linkPdf
    
    if (link == ""):
        raise Exception(f"Non è stata pubblicata una variazione orario per il `{dataSelezionata}`")

    if (onlyLink):
        return link

    # Se l'ultima volta che è stato scaricato risale a più di 10 minuti fa non scaricarlo di nuovo
    response = requests.get(link)
    with open(f'pdfScaricati/{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)

    return f'pdfScaricati/{link[link.rindex("/")+1:]}'


def formattazionePdf(percorsoPdf: str, nomeOutput: str, gradi: int, lattice):
    ruotaPdf(percorsoPdf, gradi)
    
    percorsoPdf = percorsoPdf[0:percorsoPdf.rindex("/")+1] + "r" + percorsoPdf[percorsoPdf.rindex("/")+1:]
    
    semaforo.acquire()
    convert_into(percorsoPdf, f"pdfScaricati/{nomeOutput}.csv" , pages="all", lattice=lattice)
    semaforo.release()
    
def convertiMese(n: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return mesi[int(n)-1].capitalize()

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
                    roba = riga.rstrip('\n') + ","*(numeroVirgole-len(riga.split(","))) + "\n"
                    f2.write(roba) 

    if (os.path.exists(rename)):
        os.remove(csv_file)
        os.rename(rename,csv_file)
    
    return csv_file



# Rigorosamente copia-incollato da internet
# Sauce: https://www.johndcook.com/blog/2015/05/01/rotating-pdf-pages-with-python/
def ruotaPdf(percorsoPdf: str, gradi: int):
    semaforo.acquire()

    pdf_in = open(percorsoPdf, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_in)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pagenum in range(pdf_reader.numPages):
        page = pdf_reader.getPage(pagenum)
        page.rotateClockwise(gradi)
        pdf_writer.addPage(page)

    pdf_out = open(percorsoPdf[0:percorsoPdf.rindex("/")+1] + "r" + percorsoPdf[percorsoPdf.rindex("/")+1:], 'wb')
    pdf_writer.write(pdf_out)
    pdf_out.close()
    pdf_in.close()
    
    semaforo.release()
    


def leggiPdf(giorno: str, volta: int) -> list[DocenteAssente] | str:

    # try:
    #     percorsoPdf = scaricaPdf(giorno)
    # except Exception as e:
    #     return str(e)
    #percorsoPdf = "pdfScaricati/Variazioni-orario-MERCOLEDI-5-OTTOBRE-2022-1.pdf"
    percorsoPdf = "pdfScaricati/Variazioni-orario-MARTEDI-4-OTTOBRE-2022-3.pdf"


    if (volta == 1):
        formattazionePdf(percorsoPdf,giorno,90,True)
    elif (volta == 2):
        formattazionePdf(percorsoPdf,giorno,-90,False)


    docentiAssenti: list[DocenteAssente] = []
    semaforo.acquire()
    asd = pd.read_csv(clean_up(f"pdfScaricati/{giorno}.csv"))
    semaforo.release()
    daRimuovere = asd.columns[0]

    try:
        if volta == 1:
            for riga in asd.values:
                riga: str
                if (riga[0] == daRimuovere):
                    continue
                #   0      1           2               3           4   5         6         7   8
                # ['2' '3I\r(69)' 'Spirito F.' 'Collaboratore 1.' '-' 'NO' 'Sorveglianza' nan nan]
                docentiAssenti.append(DocenteAssente(int(riga[0]),riga[1].replace("\r",""),riga[2],riga[3] + " | " + riga[4],riga[6]))  
        elif volta == 2:
            i = 0
            daTogliere = 0
            while i < len(asd.values):
                if (i+1 < len(asd.values) and math.isnan(asd.values[i+1][1])):
                    i+=1
                    daTogliere = 1
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


        return docentiAssenti

    except Exception as e:
        print(str(e))
        if volta == 1:
            return leggiPdf(giorno, 2)
        return f"C'è stato un problema col pdf, ti mando il link diretto al download\n\n{link}"

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
            return f"Variazioni orario per il `{giorno}`\n\n{stringa}"
    except Exception as e:
        print(str(e))
        return f"C'è stato un problema col pdf, ti mando il link diretto al download\n\n{link}"
    
def Main(classeDaCercare: str, giorno: str = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m"),onlyLink=False):
    #TODO Quando due utenti fanno un comando allo stesso tempo, non si deve bloccare


    if giorno == "domani" or giorno == "":
        giorno = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime("%d-%m")
    elif giorno == "oggi":
        giorno = datetime.datetime.now().strftime("%d-%m")


    giorno = giorno.replace("/","-")
    if (onlyLink):
        return scaricaPdf(giorno,True)
    
    docentiAssenti = leggiPdf('0' + giorno if not len(giorno.split('-')[0]) == 2 else giorno,1)
    

    if type(docentiAssenti) == type(""):
        return docentiAssenti
    
    return CercaClasse(classeDaCercare, docentiAssenti, giorno)

def CancellaCartellaPdf():
    filelist = [ f for f in os.listdir("pdfScaricati/")]
    for f in filelist:
        os.remove(os.path.join(filelist, f))

# Da risolvere il problema col mese
if __name__ == "__main__":
    print(Main("4E","4-10"))
    #print(Main("1E"))