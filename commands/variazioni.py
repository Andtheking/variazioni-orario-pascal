from requirements import *
from api.main import variazioni_by_date, search_class

async def variazioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    re_date = re.compile(r"\d{1,2}[\/-]\d{1,2}")
    re_classe = re.compile(r"[1-5][A-Z]", re.IGNORECASE)
    re_prof = re.compile("\"(.+)\"")
    
    text = context.matches[0].groupdict()['params'].strip()
    
    # print(context.matches[0].groupdict())
    date = (re_date.findall(text) or [None])[0]
    classe = (re_classe.findall(text) or [None])[0]
    prof = (re_prof.findall(text) or [None])[0]
    
    sep_char = re.search(r'[^0-9]', date).group(0)  # Trova il separatore
    date = sep_char.join(part.zfill(2) for part in date.split(sep_char))

    await rispondi(update.effective_message, search_class(variazioni_by_date(date=date),classe))