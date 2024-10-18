# Commands

from commands.doAlways import middleware
from commands.admin import addAdmin, removeAdmin
from commands.variazioni import variazioni
from commands.impostaClasse import impostaClasse
from commands.classe import classe
from commands.rimuoviClasse import rimuoviClasse


# Jobs
from jobs.send_logs import send_logs_channel
from jobs.initialize import initialize
from jobs.check_website import check_school_website