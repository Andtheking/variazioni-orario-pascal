import PyPDF2, re
from .pdf_hash import get_pdf_hash

from utils.log import log
from utils.jsonUtils import toJSONFile, fromJSONFile, toJSON
from utils.format_output import format_variazione

from models.models import Variazione, Pdf

import datetime
def LeggiPDF(pdf_path):
    REGEX = r"^(?P<ora>[1-6])\s*(?P<classe>(?:[1-5](?:[A-Z]|BIO))| POTENZIAMENTO| SPORTELLO)(?:\((?P<aula>.+?)\)|\s*)(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"
    REGEX2 = r"^(?P<ora>[1-6])\s*(?P<classe>(?:[1-5](?:[A-Z]|BIO))| POTENZIAMENTO| SPORTELLO)\s*(?:(?P<aula>[^ ]+)|\s*)\s*(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"
    REGEX3 = r"(?P<ora>[1-6])\s*(?P<classe>(?:[1-5](?:[A-Z]|BIO))| POTENZIAMENTO| SPORTELLO)\s*(?:(?P<aula>[^ ]+)|\s*)\s*(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>[^_]+)"
    
    a = PyPDF2.PdfReader(pdf_path)
    
    api_output = []
    dicts = []
    for p in a.pages:
        t = p.extract_text()
        matches = re.finditer(REGEX3, t)
        dicts.extend([m.groupdict() for m in matches])
        pass
            
    return dicts

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
        try:
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
                v.hash_variazione = str(hashlib.sha1((format_variazione(v) + date + str(datetime.datetime.now().year)).encode("utf-8")).hexdigest())
                print(v.hash_variazione)
                v.save()
        except Exception as e:
            pdf.delete()
            raise Exception(f"Salvataggio nel DB delle variazione non riuscito: {e}")
    
    return pdf