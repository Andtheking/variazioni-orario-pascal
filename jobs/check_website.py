from requirements import *
import requests
from bs4 import BeautifulSoup

from api.get_pdf import scaricaPdf
from api.read_pdf import PDF_db

from utils.jsonUtils import fromJSONFile
from utils.format_output import format_variazione

URL = fromJSONFile('secret/utils.json')['URL']
lastcheck = [""]

from telegram.error import Forbidden

import time
from datetime import datetime

TEST = False

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

    log("Il sito è stato modificato")
    lastcheck[0] = mod[0]

    start = time.time()
    if not TEST:
        l = download_pdfs(soup) # in "l" ci saranno i PDF del db.
    else:
        l = Pdf.select().where(Pdf.date << ['01-01','02-01'])
    end = time.time()
    
    log(f"Impiegato {end-start} per controllare pdf dal sito.")
    
    for pdf in l:
        log(f"PDF numero {pdf.id}, data: {pdf.date}")

    utente: Utente
    for utente in Utente.select():
        if not utente.notifiche_live or (not utente.classe and not utente.prof):
            continue
        
        variazioni_utente: list[Variazione] = Variazione.select().join(Pdf).where((Variazione.classe == utente.classe) & (Pdf.id << [k.id for k in l])).order_by(Pdf.date)
        output_by_date: dict[str, list[str,list[Variazione]]] = {}

        for v in variazioni_utente:
            date = v.pdf.date
            h = v.hash_variazione
            
            already_sent = (VariazioniInviate
                .select()
                .join(Utente, on=(VariazioniInviate.utente == Utente.id))
                .where((Utente.id == utente.id) &  (VariazioniInviate.hash_messaggio == v.hash_variazione))
            )
            
            if already_sent:
                continue

            if date not in output_by_date:
                output_by_date[date] = [f"Variazioni per la {v.classe} il {date}\n\n",[]]

            output_by_date[date][0] += format_variazione(v)
            output_by_date[date][1].append(v)
        
        for date, message in output_by_date.items():
            message, v = (message[0], message[1])
            try:
                await context.bot.send_message(
                    chat_id=utente.id,
                    text=message.strip(),  
                    parse_mode=ParseMode.HTML
                )
                
                for a in v:
                    VariazioniInviate.create(variazione=a, utente=utente, hash_messaggio=a.hash_variazione)
            except Exception as e:
                error = f"Invio della notifica live a {utente.username} ({utente.id}) non riuscito."
                
                if e is Forbidden:
                    error += "Probabilmente ha bloccato il bot."
                
                error += '\n\n' + str(e)
                
                log(error, send_with_bot=(not (e is Forbidden)), tipo='errore')
            
    
def download_pdfs(soup: BeautifulSoup) -> list[Pdf]:
    soup = soup.find_all("a")
    listaPdf: list[str] = [a['href'] for a in soup if "pdf" in a['href']]
    pdfs = []
    for link in listaPdf:
        path = scaricaPdf(link)
        x = None
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
    match = re.search(r'(\d{2})-(\w+)', nome_pdf)
    if match:
        giorno = match.group(1)  # Prendi il giorno
        mese = match.group(2)     # Prendi il mese

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
            return f"00{giorno}"[-2:] + "-" + f"00{mese_numero}"[-2:]  # Restituisci la stringa formattata
    return None  # Se non c'è corrispondenza, restituisci None