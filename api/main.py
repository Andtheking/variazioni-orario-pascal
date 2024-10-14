from datetime import datetime, timedelta
from .get_pdf import allPdfsByDate
from .read_pdf import PDFJson
    
def variazioni_by_date(date=None):
    if date is None:
        date = (datetime.now() +
                  timedelta(days=1)).strftime("%d-%m")
        
    paths = allPdfsByDate(date)
    
    if not paths:
        return None
    
    x = []
    for p in paths:
        x.append(PDFJson(p))

    return x

def search_class(json, classe):
    output = []
    for pdf in json:
        # Uso append e non extend per separare i vari pdf diversi in elementi diversi della lista
        output.append([record for record in pdf if record['classe'] == classe])
    return output

if __name__ == "__main__":
    print(search_class(variazioni_by_date("14-10"),"2M"))