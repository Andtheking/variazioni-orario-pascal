import hashlib

def get_pdf_hash(filepath):
    """
    Calcola l'hash del contenuto del pdf
    Thanks chat gpt
    """
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as pdf:
        buf = pdf.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = pdf.read(BLOCKSIZE)
    return hasher.hexdigest()