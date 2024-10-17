from models.models import Variazione

TEMPLATE = (
            "Prof assente: <code>{prof_assente}</code>\n"
            "Ora: <code>{ora}</code>\n"
            "Sostituto: <code>{sostituto_1} e {sostituto_2}</code>\n"
            "Classe(Aula): <code>{classe}({aula})</code>\n"
            "Note: <code>{note}</code>\n\n"
)

def format_variazione(variazione: Variazione):
    return TEMPLATE.format(
        prof_assente = variazione.prof_assente,
        ora = variazione.ora,
        sostituto_1 = variazione.sostituto_1 or '-',
        sostituto_2 = variazione.sostituto_2 or '-',
        classe = variazione.classe,
        aula = variazione.aula or '?',
        note = variazione.note or 'None'
    )