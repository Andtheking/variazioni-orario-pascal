from requirements import *
import requests
from bs4 import BeautifulSoup

from api.get_pdf import scaricaPdf
from api.read_pdf import PDFJson

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



    l = download_pdfs(soup) # in "l" ci saranno i PDF letti e trasformati in JSON.
    
    for pdf in l:
        pass
    # if len(l) == 0:
    #     log("Nessun nuovo pdf")
    #     return
    
    
def download_pdfs(soup: BeautifulSoup):
    soup = soup.find_all("a")
    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]
    pdfs = []
    for link in listaPdf:
        x = PDFJson(scaricaPdf(link))
        if x is not None:
            pdfs.append(x)
    return pdfs