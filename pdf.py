from tabula import read_pdf, convert_into
import requests, pandas as pd
from bs4 import BeautifulSoup
import PyPDF2

url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"



def scaricaPdf(dataSelezionata: str) -> str: 
    """
    Scarica il pdf dal sito del Pascal
    
    Args:
        dataSelezionata Data del giorno scelto in formato giorno-mese

    Return:
        (str) percorso pdf scaricato
    """


    if ('-' in dataSelezionata):
        data = dataSelezionata.split('-')

    
    data[0] = '0'+data[0] if int(data[0]) < 10 else data[0]
    data[1] = convertiMese(data[1])


    soup = BeautifulSoup(requests.get(url).content, "html.parser").find_all("a")

    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]

    link = ""
    for linkPdf in listaPdf:
        if f"-{data[0]}-" in linkPdf.lower():
            link = linkPdf

    if (link == ""):
        return f"Non ho trovato nulla per il giorno {data[0]} {data[1].capitalize()}"

    response = requests.get(link)
    
    with open(f'pdfScaricati/{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)
    
    return f'pdfScaricati/{link[link.rindex("/")+1:]}'


def convertiMese(n):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre","dicembre"]
    return mesi[int(n)-1]



def leggiPdf(percorsoPdf: str, classeDaCercare):
    
    #df: list[pd.DataFrame or dict] = read_pdf(percorsoPdf,pages="all", lattice=True)
    ruotaPdf(percorsoPdf)
    percorsoPdf = percorsoPdf[0:percorsoPdf.rindex("/")+1] + "r" + percorsoPdf[percorsoPdf.rindex("/")+1:]
    df = convert_into(percorsoPdf, "pdfScaricati/output.csv" , pages="all", lattice=True)
    
    asd = pd.read_csv("pdfScaricati/output.csv")
    titoli = asd.head()

    daRimuovere = asd.columns[0]
    

    for riga in asd.values:
        if (riga[0] == daRimuovere):
            continue
        if (classeDaCercare in riga[1]):
            print(riga)




    #print(df[0])

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
    

    
def main(classeToFind: str):
    pass

if __name__ == "__main__":
    leggiPdf(scaricaPdf("1-10"), "3I")
    main("3I")



   
    