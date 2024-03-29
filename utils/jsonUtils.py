import jsonpickle, os
from threading import Semaphore

semScrittura = Semaphore(1)
sem = Semaphore(1)

def toJSON(file: str, obj):
    semScrittura.acquire()
    with open(file,"w",encoding="utf8") as f:
        f.write(jsonpickle.encode(obj))
    semScrittura.release()
        
l = 0
def fromJSON(file: str, ifFileEmpty = "[]"):
    global l
    
    sem.acquire()
    l+=1
    if l == 1:
        semScrittura.acquire()
    sem.release()
    
    
    if not os.path.exists(file):
        open(file,"w",encoding="utf8").close()
    
    with open(file,"r",encoding="utf8") as f:
        text = f.read()
        thing = jsonpickle.decode(text if text != "" else ifFileEmpty)
        
    sem.acquire()
    l-=1
    if l == 0:
        semScrittura.release()
    sem.release()
    
    return thing