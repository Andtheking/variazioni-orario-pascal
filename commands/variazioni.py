from requirements import *
from api.main import variazioni_by_date
from datetime import datetime, timedelta
from utils.format_output import format_variazione

async def variazioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    re_date = re.compile(r"\d{1,2}[\/-]\d{1,2}")
    re_classe = re.compile(r"[1-5][A-Z]", re.IGNORECASE)
    re_prof = re.compile("\"(.+)\"")
    
    text = context.matches[0].groupdict()['params'].strip()
    
    # print(context.matches[0].groupdict())
    u = Utente.get_by_id(update.effective_user.id)
    
    date = (re_date.findall(text) or [(datetime.now() + timedelta(days=1)).strftime("%d-%m")])[0]
    classe = (re_classe.findall(text) or [None])[0] 
    prof = (re_prof.findall(text) or [None])[0] 
    modalita = u.modalita
    
    if date:
        sep_char = re.search(r'[^0-9]', date).group(0)  # Trova il separatore
        date = sep_char.join(part.zfill(2) for part in date.split(sep_char))

    if not classe and not prof:
        if modalita == 'studente':
            classe = u.classe
        elif modalita == 'prof':
            prof = u.prof
    elif classe and prof:
        if modalita == 'studente':
            prof = None
        elif modalita == 'prof':
            classe = None
     
    variazioni_giornata = variazioni_by_date(date=date)
    
    if not variazioni_giornata:
        await rispondi(update.effective_message, f"Non ho trovato nessun PDF per il {date}.")
        return
    
    variazioni_classe = []
    for pdf in variazioni_giornata:
        if classe:
            result = list(Variazione.select().join(Pdf).where((Variazione.classe == classe) & (Pdf.id == pdf.id)))
            if result:
                variazioni_classe.append(result)
        elif prof:
            result = list(Variazione.select().join(Pdf).where(((Variazione.sostituto_1 == prof) | (Variazione.sostituto_2 == prof)) & (Pdf.id == pdf.id)))
            if result:
                variazioni_classe.append(result)
        
    
    risposta = ""
    who = f'la <code>{classe}</code>' if classe else f'il prof <code>{prof}</code>'
    if len(variazioni_classe) > 0:
        risposta = f"Variazioni orario per {who} il <code>{date}</code>\n\n{format_output(variazioni_classe)}"
    else:
        risposta = f"Non ho trovato nessuna variazione per {who} il <code>{date}</code>."
    
    await rispondi(update.effective_message, risposta)
    
# TODO Rendere più carino il messaggio, emoji?
def format_output(pdfs):
    output = ""
    for i,pdf in enumerate(pdfs):
        if i > 0:
            output += "Ho trovato un altro PDF\n\n"
        
        for variazione in pdf:
            output += format_variazione(variazione)
    
    return output.strip()