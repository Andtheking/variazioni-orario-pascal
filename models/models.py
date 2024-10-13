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
    
class Chat(BaseModel):
    id = IntegerField(primary_key=True)
    title = TextField(null=True)

if __name__ == '__main__':
    db.drop_tables([Utente, Chat])
    db.create_tables([Utente, Chat])