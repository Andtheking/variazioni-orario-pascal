from requirements import *
from api.main import variazioni_by_date
from datetime import datetime, timedelta

async def variazioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    re_date = re.compile(r"\d{1,2}[\/-]\d{1,2}")
    re_classe = re.compile(r"[1-5][A-Z]", re.IGNORECASE)
    re_prof = re.compile("\"(.+)\"")
    
    text = context.matches[0].groupdict()['params'].strip()
    
    # print(context.matches[0].groupdict())
    date = (re_date.findall(text) or [(datetime.now() + timedelta(days=1)).strftime("%d-%m")])[0]
    classe = (re_classe.findall(text) or [None])[0]
    prof = (re_prof.findall(text) or [None])[0]
    
    if date:
        sep_char = re.search(r'[^0-9]', date).group(0)  # Trova il separatore
        date = sep_char.join(part.zfill(2) for part in date.split(sep_char))

    variazioni_giornata = variazioni_by_date(date=date)
    
    if not variazioni_giornata:
        await rispondi(update.effective_message, f"Non ho trovato nessun PDF per il {date}.")
        return
    
    variazioni_classe = []
    for pdf in variazioni_giornata:
        variazioni_classe.append(Variazione.select().join(Pdf).where((Variazione.classe == classe) & (Pdf.id == pdf.id)))
        
    
    if len(variazioni_classe) > 0:
        await rispondi(update.effective_message, f"Variazioni orario per la <code>{classe}</code> il <code>{date}</code>\n\n{format_output(variazioni_classe)}")
    else:
        await rispondi(update.effective_message, f"Non ho trovato nessuna variazione per la <code>{classe}</code> per il <code>{date}</code>.")
        
# TODO Rendere più carino il messaggio, emoji?
def format_output(pdf_db_entry):
    output = ""
    for i,pdf_db_entry in enumerate(pdf_db_entry):
        if i > 0:
            output += "Ho trovato un altro PDF\n\n"
        for variazione in pdf_db_entry:
            output += (
                f"Prof assente: <code>{variazione.prof_assente}</code>\n"
                f"Ora: <code>{variazione.ora}</code>\n"
                f"Sostituto: <code>{variazione.sostituto_1 or '-'} e {variazione.sostituto_2 or '-'}</code>\n"
                f"Classe(Aula): <code>{variazione.classe}({variazione.aula})</code>\n"
                f"Note: <code>{variazione.note}</code>\n\n"
            )
    
    return output.strip()