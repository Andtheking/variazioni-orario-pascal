import PyPDF2, re
from .pdf_hash import get_pdf_hash

from utils.log import log
from utils.jsonUtils import toJSONFile, fromJSONFile, toJSON

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
        x.update({hsh: LeggiPDF(pdf_path), "read_date": datetime.datetime.now()})
        toJSONFile('variazioni.json',x)
    return x[hsh]

if __name__ == '__main__':
    PDFJson(__file__[:__file__.rindex('\\')+1] + 'pdf.pdf')