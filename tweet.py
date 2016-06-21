"""Downloads gun incidents from gun violence archive and tweets each incident to representatives"""
import sqlite3
import requests

from bs4 import BeautifulSoup

DBNAME = 'incidents.db'
def get_incidents(url):
    """Fetches gun incident html"""

    site = requests.get(url)
    soup = BeautifulSoup(site.text, "html.parser")
    incidents_html = soup.find('table').findAll('tr')
    incidents = [incident.findAll('td') for incident in incidents_html[1:]]

    print('site fetched')
    return incidents


def insert_incidents(incidents):
    """Inserts gun incidents into sqlite db"""

    #con = sqlite3.connect(DBNAME)
    con = sqlite3.connect('incidents.db')
    base_url = 'http://www.gunviolencearchive.org'
    for incident in incidents:
        try:
            with con:
                date = incident[0].text
                state = incident[1].text
                city = incident[2].text
                address = incident[3].text
                killed = incident[4].text
                injured = incident[5].text
                incident_url = incident[6].find('li', class_='0').find('a').attrs['href']
                incident_url = ''.join([base_url, incident_url])
                source_url = incident[6].find('li', class_='1').find('a').attrs['href']

                data = (date, state, city, address, killed, injured, incident_url, source_url)

                con.execute('INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?)', data)
                print('inserted', data)
        except sqlite3.IntegrityError:
            print('dup entry', data)

    return True


def main():
    """Main function"""

    url = 'http://www.gunviolencearchive.org/last-72-hours'
    incidents = get_incidents(url)
    data = insert_incidents(incidents)

    return data

if __name__ == "__main__":
    main()
