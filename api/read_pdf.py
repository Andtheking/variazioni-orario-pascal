import PyPDF2, re
from .pdf_hash import get_pdf_hash

from utils.log import log
from utils.jsonUtils import toJSONFile, fromJSONFile, toJSON
from utils.format_output import format_variazione

from models.models import Variazione, Pdf

import datetime
def LeggiPDF(pdf_path):
    REGEX = r"^(?P<ora>[1-6])\s*(?P<classe>(?:[1-5](?:[A-Z]|BIO))| POTENZIAMENTO)(?:\((?P<aula>.+?)\)|\s*)(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"
    a = PyPDF2.PdfReader(pdf_path)
    
    api_output = []
    for p in a.pages:
        t = p.extract_text('\n')
        lines = t.replace('\n(','(').split('\n')
        # print("\n".join(lines))
        i = 0
        for line in lines:
            m = re.search(REGEX, line)
            if m:
                api_output.append({key: (value.strip() if value else None) for key, value in m.groupdict().items()})
                i+=1
        if len(lines) != i+2: # i+2 rappresenta "Righe lette + 2", 2 che sarebbero l'intestazione"
            log(f"C'è un problema con il PDF {pdf_path}",tipo='warning', send_with_bot=True) 
            log("<$EOL$>".join(lines),tipo='warning', send_with_bot=True, only_file=True) 
            raise Exception(f"PDF: Errore con la lettura del pdf \"{pdf_path}\"")
            
    return api_output

def PDFJson(pdf_path):
    x = fromJSONFile('variazioni.json', r'{}')
    hsh = get_pdf_hash(pdf_path)
    if not hsh in x:
        log('Nuovo pdf')
        x.update({hsh: LeggiPDF(pdf_path), "read_date": datetime.datetime.now(), "sent_date": None})
        toJSONFile('variazioni.json',x)
    return x[hsh]

import hashlib

def PDF_db(pdf_path, date):
    hsh = get_pdf_hash(pdf_path)
    pdf = Pdf.get_or_none(Pdf.pdf_hash_key == hsh)
    
    if not pdf:
        log('Nuovo pdf')
        json = LeggiPDF(pdf_path)
            
        
        pdf = Pdf(pdf_hash_key=hsh, date=date)
        pdf.save()
        for variazione in json:
            v = Variazione(
                ora = variazione['ora'],
                classe = variazione['classe'],
                aula = variazione['aula'],
                prof_assente = variazione['prof_assente'],
                sostituto_1 = variazione['sostituto_1'],
                sostituto_2 = variazione['sostituto_2'],
                pagamento = variazione['pagamento'],
                note = variazione['note'],
                pdf = pdf
            )
            print(format_variazione(v) + date + str(datetime.datetime.now().year))
            v.hash_variazione = str(hashlib.sha1(format_variazione(v) + date + str(datetime.datetime.now().year)))
            print(v.hash_variazione)
            v.save()
    
    return pdf