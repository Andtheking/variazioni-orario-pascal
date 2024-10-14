from requirements import *
import requests
from bs4 import BeautifulSoup

from api.get_pdf import scaricaPdf
from api.read_pdf import PDF_db

from utils.jsonUtils import fromJSONFile

URL = fromJSONFile('secret/utils.json')['URL']
lastcheck = [""]

async def check_school_website(context: ContextTypes.DEFAULT_TYPE):
    global lastcheck
    Ok = False 
    while not Ok:
        try:
            response = requests.get(URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            Ok = True
        except:
            Ok = False
        
    mod = soup.find_all(property="article:modified_time")

    if lastcheck[0] == mod[0]:
        return

    log("Il sito è stato modificato", True, 'info')



    l = download_pdfs(soup) # in "l" ci saranno i PDF del db.
    
    for pdf in l:
        log(pdf)
        pass
    
    
    # if len(l) == 0:
    #     log("Nessun nuovo pdf")
    #     return
    
    
def download_pdfs(soup: BeautifulSoup) -> list[Pdf]:
    soup = soup.find_all("a")
    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]
    pdfs = []
    for link in listaPdf:
        path = scaricaPdf(link)
        try:
            x = PDF_db(path, estrai_data(path))
        except Exception as e:
            log(f"{e}", True, 'errore')
        if x is not None:
            pdfs.append(x)
    return pdfs


# Grande come sempre ChatGPT
def estrai_data(nome_pdf):
    # Usa una regex per trovare il giorno e il mese nel nome del file
    match = re.search(r'(\d{1,2})-(\w+)-di-(\w+)-(\d{1,2})-(\w+)-(\d{4})', nome_pdf)
    if match:
        giorno = match.group(1)  # Prendi il giorno
        mese = match.group(3)     # Prendi il mese

        # Mappa dei mesi
        mesi = {
            'gennaio': '01',
            'febbraio': '02',
            'marzo': '03',
            'aprile': '04',
            'maggio': '05',
            'giugno': '06',
            'luglio': '07',
            'agosto': '08',
            'settembre': '09',
            'ottobre': '10',
            'novembre': '11',
            'dicembre': '12'
        }
        
        mese_numero = mesi.get(mese.lower())  # Ottieni il numero del mese
        if mese_numero:
            return f"00{giorno}"[-2:] - f"00{mese_numero}"[-2:]  # Restituisci la stringa formattata
    return None  # Se non c'è corrispondenza, restituisci None