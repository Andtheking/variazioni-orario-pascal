# Questa funzione (gentilmente concessa da ChatGPT) la avvierò sul mio PC giusto quando cambio 
# i comandi, non la avvierò sulla macchina che uso come host.


from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import time
import subprocess
import urllib.parse

# Percorso del driver per Chrome (modifica il percorso se necessario)
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
chrome_driver_path = r"C:\Users\andre\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\chromedriver_binary\chromedriver.exe"

# Inizializza il driver di Selenium
service = Service(executable_path=chrome_driver_path)
options = ChromeOptions()
options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"


path = 'utils/commands_images/'

import re
def get_regex_image(regexes: dict[str, list[str]]):
    driver = webdriver.Chrome(service=service, options=options)
    # Apri la pagina regexper con la tua regex
    for command,regs in regexes.items():
        for i,reg in enumerate(regs):
            reg = re.sub(r'\?P<[^>]+>','', reg)
            rencoded = urllib.parse.quote_plus(reg)
            regex_url = f"https://regexper.com/#{rencoded}"
            driver.get(regex_url)

            # Aspetta che la pagina carichi l'immagine (regola il tempo se necessario)
            print("Waiting 2 seconds...")
            time.sleep(.5)

            # Trova l'elemento immagine generato
            svg_element = driver.find_element(By.CSS_SELECTOR, ".svg svg")
            svg_code = svg_element.get_attribute('outerHTML')

            inkscape_path = r"\Program Files\Inkscape\bin\inkscape.exe"
            with open(path+'file.svg', 'w', encoding='utf8') as f:
                f.write(svg_code)

            command = [f'{inkscape_path}', '--export-type=png', f'--export-filename={path}{command}_{i}.png', f'{path}file.svg']
            subprocess.Popen(command)

    # Chiudi il driver
    driver.quit()