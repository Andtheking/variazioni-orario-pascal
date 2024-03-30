from .get_pdf import allPdfsByDate
from .read_pdf import PDFJson

def main(date):
    paths = allPdfsByDate(date)
    x = []
    for p in paths:
        x.append(PDFJson(p))
    return x
        
if __name__ == '__main__':
    print(main('03-04'))
    