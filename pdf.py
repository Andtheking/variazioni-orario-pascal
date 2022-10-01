from tabula import read_pdf, convert_into
import requests, pandas as pd
from bs4 import BeautifulSoup
import PyPDF2
import os


url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"



def scaricaPdf(dataSelezionata: str) -> str: 
    """
    Scarica il pdf dal sito del Pascal
    
    Args:
        dataSelezionata Data del giorno scelto in formato giorno-mese

    Return:
        (str) percorso pdf scaricato
    """

    # L'if si può estendere con degli elif per aggiungere più separatori
    if ('-' in dataSelezionata):
        data = dataSelezionata.split('-')

    
    data[0] = '0' + data[0] if int(data[0]) < 10 else data[0] # In caso il numero è minore di 10 aggiungi lo 0 prima, es: 08,09,10


    soup = BeautifulSoup(requests.get(url).content, "html.parser").find_all("a")

    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]

    link = ""
    for linkPdf in listaPdf:
        if f"-{data[0]}-" in linkPdf.lower():
            link = linkPdf

    if (link == ""):
        return f"Non ho trovato nulla per il giorno {data[0]}/{data[1]}"

    response = requests.get(link)
    
    with open(f'pdfScaricati/{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)
    
    return f'pdfScaricati/{link[link.rindex("/")+1:]}'

class DocenteAssente:
    def __init__(self, ora: int, classeAula: str, profAssente: str, sostituti: str, note: str):
        self.ora = ora # 1
        self.classeAula = classeAula # "4I(78)"
        self.profAssente = profAssente # "Nome C."
        self.sostituti = sostituti # "Nome C."
        self.note = note # "La classe entra alla 2° ora"

def formattazionePdf(percorsoPdf: str, nomeOutput: str):

    ruotaPdf(percorsoPdf)
    os.remove(percorsoPdf)
    
    percorsoPdf = percorsoPdf[0:percorsoPdf.rindex("/")+1] + "r" + percorsoPdf[percorsoPdf.rindex("/")+1:]
    
    convert_into(percorsoPdf, f"pdfScaricati/{nomeOutput}.csv" , pages="all", lattice=True)
    os.remove(percorsoPdf)

    

# Rigorosamente copia-incollato da internet
# Sauce: https://www.johndcook.com/blog/2015/05/01/rotating-pdf-pages-with-python/
def ruotaPdf(percorsoPdf: str):
    pdf_in = open(percorsoPdf, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_in)
    pdf_writer = PyPDF2.PdfFileWriter()

    for pagenum in range(pdf_reader.numPages):
        page = pdf_reader.getPage(pagenum)
        page.rotateClockwise(90)
        pdf_writer.addPage(page)

    pdf_out = open(percorsoPdf[0:percorsoPdf.rindex("/")+1] + "r" + percorsoPdf[percorsoPdf.rindex("/")+1:], 'wb')
    pdf_writer.write(pdf_out)
    pdf_out.close()
    pdf_in.close()
    
def leggiPdf(giorno: str):
    # Giorno per esempio è "1-10" → 1 Ottobre
    

    if not os.path.exists(f"pdfScaricati/{giorno}.csv"):
        formattazionePdf(scaricaPdf(giorno),giorno)
    
    docentiAssenti: list[DocenteAssente] = []
    asd = pd.read_csv(f"pdfScaricati/{giorno}.csv")
    daRimuovere = asd.columns[0]

    for riga in asd.values:
        riga: str
        if (riga[0] == daRimuovere):
            continue
        #   0      1           2               3           4   5         6         7   8
        # ['2' '3I\r(69)' 'Spirito F.' 'Collaboratore 1.' '-' 'NO' 'Sorveglianza' nan nan]
        docentiAssenti.append(DocenteAssente(int(riga[0]),riga[1].replace("\r",""),riga[2],riga[3] + " | " + riga[4],riga[6]))
    
    return docentiAssenti

def CercaClasse(classe: str, docentiAssenti: list[DocenteAssente]):
    stringa = ""
    
    for docente in docentiAssenti:
        if classe in docente.classeAula:
            stringa += f"Ora: {docente.ora}\nClasse(Aula): {docente.classeAula}\nDocente assente: {docente.profAssente}\nSostituito da: {docente.sostituti.replace(' | ', ' e ')}\nNote: {docente.note}\n\n" 

    print (stringa)
    
def main(classeDaCercare: str, giorno: str):
    docentiAssenti = leggiPdf(giorno)
    CercaClasse(classeDaCercare, docentiAssenti)


    

if __name__ == "__main__":
    print("Scrivi la classe e il giorno")
    main(input(), input())



   
    