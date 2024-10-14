from peewee import *

# Connettiamo al database SQLite
db = SqliteDatabase('secret/Database.db')

class BaseModel(Model):
    class Meta:
        database = db
        
class Utente(BaseModel):
    id = IntegerField(primary_key=True)
    username = TextField(null=True)
    admin = BooleanField(default=False)
    classe = TextField(null=True)
    notifiche_mattina = BooleanField(default=False)
    notifiche_sera = BooleanField(default=False)
    notifiche_live = BooleanField(default=False)
    notifiche_nessunaVar = BooleanField(default=False)
    modalita = TextField(default="studente")
    prof = TextField(null=True)
    
    

class Pdf(BaseModel):
    pdf_hash_key = TextField(null=False, unique=True)
    sent = BooleanField(default=False)

class Variazione(BaseModel):
    ora = TextField(null=True, unique=False)
    classe = TextField(null=True, unique=False)
    aula = TextField(null=True, unique=False)
    prof_assente = TextField(null=True, unique=False)
    sostituto_1 = TextField(null=True, unique=False)
    sostituto_2 = TextField(null=True, unique=False)
    pagamento = TextField(null=True, unique=False)
    note = TextField(null=True, unique=False)
    pdf = ForeignKeyField(Pdf, backref='variazioni')  # Colonna per il pdf da cui è stata estrapolata la variazione
    hash_variazione = TextField(unique=False)
    
class Chat(BaseModel):
    id = IntegerField(primary_key=True)
    title = TextField(null=True)

if __name__ == '__main__':
    db.drop_tables([Pdf, Variazione])
    db.create_tables([Pdf, Variazione])