import PyPDF2, re
from .pdf_hash import get_pdf_hash

from utils.log import log
from utils.jsonUtils import toJSONFile, fromJSONFile, toJSON

from models.models import Variazione, Pdf

import datetime
def LeggiPDF(pdf_path):
    REGEX = r"^(?P<ora>[1-6])\s*(?P<classe>(?:[1-5]([A-Z]|BIO))| POTENZIAMENTO)\((?P<aula>.+?)\)(?P<prof_assente>.+?\s.+?\s)(?P<sostituto_1>(?:- |.+?\s.+?\s))(?P<sostituto_2>(?:- |.+?\s.+?\s))(?P<pagamento>.+?(?:\s|$))(?P<note>.+)?"
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
                api_output.append({key: value.strip() for key, value in m.groupdict().items()})
                i+=1
        if len(lines) != i+2:
            log("C'è un problema con i PDF.",tipo='warning', send_with_bot=True) 
            log("<$EOL$>".join(lines),tipo='warning', send_with_bot=True, only_file=True) 
            
    return api_output

def PDFJson(pdf_path):
    x = fromJSONFile('variazioni.json', r'{}')
    hsh = get_pdf_hash(pdf_path)
    if not hsh in x:
        log('Nuovo pdf')
        x.update({hsh: LeggiPDF(pdf_path), "read_date": datetime.datetime.now(), "sent_date": None})
        toJSONFile('variazioni.json',x)
    return x[hsh]

def PDF_db(pdf_path):
    hsh = get_pdf_hash(pdf_path)
    pdf = Pdf.get_or_none(Pdf.pdf_hash_key == hsh)
    
    if not pdf:
        log('Nuovo pdf')
        json = LeggiPDF(pdf_path)
        
        pdf = Pdf(pdf_hash_key=hsh)
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
            v.save()
    
    return pdf