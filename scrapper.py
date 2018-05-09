from bs4 import BeautifulSoup
import re
import requests
import threading
import time

# Name of the file to write the csv data
outputFile = 'output.csv'
# Base url of the university directory
baseurl = "https://annuaire.univ-orleans.fr"
# Max number of threads for execution
maxThreads = 200
# Lock used to block the threads while a new line is written to the file
lock = threading.Lock()

# Recusive method for parsing all the infos from a base url
def parser(url, parent):
    # Get the page for url and create the soup
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')

    # If this element is found we're in a detail page of a person -> recursion end
    table = soup.find('table', {"class": "fiche"})
    if (table):
        return
    # We retrieve the table
    table = soup.find('table')
    if (table):
        # Retrieve all the links in the table
        links = soup.select('tr > td > a')
        for link in links:
            # If the href isn't an email
            if ('[remplacer_par_at]' not in link['href']):
                # The url of the element
                url = baseurl + link['href']
                # Removing white space, carriage return and commas from the names
                nom = re.sub('[ ]{2,}', '', link.text)
                nom = nom.replace('\n', '').replace(',', '')
                # The id of the element is it's name + the parrent id separated with a .
                id = parent + "." + nom
                # Locking threads to protect file write
                lock.acquire()
                file = open(outputFile, 'ab')
                line = '{},{},{},{}\n'.format(parent, id, nom, url)
                # Printing what we write just to show progress...
                print(line)
                file.write(line.encode('utf-8'))
                file.close()
                # Finished writing to file -> remove lock
                lock.release()
                # Limiting the number of threads
                while (threading.active_count() > maxThreads):
                    time.sleep(1)
                # Start a new thread to parse the next level
                t = threading.Thread(target=parser, args=(url, id))
                t.start()


choice = input("Que voullez vous faire? \n"
               "\t-Parser toutes les composantes (1)\n"
               "\t-Récupérer uniquement l'IUT d'Orléans(2)? \n"
               "\t Quitter (Q)\n")

while choice != "1" and choice != "2" and choice != "Q":
    choice = input("Erreur, veuillez saisir 1 ou 2 (Q pour quitter)\n")
if choice == "Q":
    exit()

print("Parsing des informations, veuillez patienter")
# Write first lines of the csv -> Cols name and
file = open(outputFile, "wb")
# Adding cols name
line = "parent,id,nom,href\n"
file.write(line.encode("utf-8"))

# All composantes
if choice == "1":
    root_url = baseurl + "/RechercheParOrg/listercomposantes"
    parentName = "composantes"
# Only IUT d'Orléans
elif choice == "2":
    root_url = baseurl + "/EmployeParOrg/index/c_oid/905"
    parentName = "IUT d'Orléans (45)"

line = "," + parentName + ","  + parentName +"," + root_url + "\n"
file.write(line.encode('utf-8'))
file.close()
parser(root_url, parentName)
