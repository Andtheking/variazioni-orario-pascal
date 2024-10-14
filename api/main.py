from datetime import datetime, timedelta
from .get_pdf import allPdfsByDate
from .read_pdf import PDF_db
    
from models.models import Pdf

def variazioni_by_date(date=None) -> list[Pdf]:
    if date is None:
        date = (datetime.now() +
                  timedelta(days=1)).strftime("%d-%m")
        
    paths = allPdfsByDate(date)
    
    if not paths:
        return None
    
    x = []
    for p in paths:
        x.append(PDF_db(p, date))

    return x


if __name__ == "__main__":
    print(variazioni_by_date("15-10"),"1A")