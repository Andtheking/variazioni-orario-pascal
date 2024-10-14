from . import logger

import requests, datetime
from bs4 import BeautifulSoup


URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"
DOWNLOAD_FOLDER = 'api\\pdfs'

def ottieniLinkPdfs(dataSelezionata: str) -> list[str]:
    dataSelezionata = formattaGiorno(dataSelezionata)

    data = dataSelezionata.split('-')

    soup = BeautifulSoup(requests.get(URL).content,
                         "html.parser").find_all("a")

    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]

    link = []
    for linkPdf in listaPdf:
        if (f"-{data[0]}-" in linkPdf.lower() or f"-{data[0][1:]}-" in linkPdf.lower()) and f"{convertiMese(data[1]).lower()}" in linkPdf.lower():
            link.append(linkPdf)
    
    if (link == []):
        return None

    return link

def scaricaPdf(link: str) -> str:
    response = requests.get(link)

    with open(f'{DOWNLOAD_FOLDER}\\{link[link.rindex("/")+1:]}', 'wb') as f:
        f.write(response.content)

    return f'{DOWNLOAD_FOLDER}\\{link[link.rindex("/")+1:]}'

def allPdfsByDate(date):
    links = ottieniLinkPdfs(date)
    local_paths = []
    
    if not links:
        return None
    
    for link in links:
        local_paths.append(scaricaPdf(link))
    return local_paths

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

def convertiMese(n: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return mesi[int(n)-1].capitalize()
