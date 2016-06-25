"""Downloads gun incidents from gun violence archive and tweets each incident to representatives"""
import json
import sqlite3
import requests

from bs4 import BeautifulSoup
from pyshorteners import Shortener
import tweepy

DBNAME = 'incidents.db'
SHORTENER = Shortener('Tinyurl')

def connect_to_twitter():
    """
    Authenticates with twitter and returns api object
    """

    with open('twitter_api.keys', 'r') as twitter_api_keys:
        data = json.load(twitter_api_keys)

    consumer_key = data['consumer_key']
    consumer_secret = data['consumer_secret']
    key = data['key']
    secret = data['secret']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(key, secret)

    api = tweepy.API(auth)
    return api


def get_incidents(url):
    """Fetches gun incident html"""

    site = requests.get(url)
    soup = BeautifulSoup(site.text, "html.parser")
    incidents_html = soup.find('table').findAll('tr')
    incidents = [incident.findAll('td') for incident in incidents_html[1:]]

    print('site fetched')
    return incidents


def build_status(data):
    """Builds and returns status string"""
    _, state, city, _, killed, injured, incident_url, source_url = data
    status_string = 'Gun incident reported: '
    if killed and injured:
        status_string += '{} dead and {} injured '.format(killed, injured)
    elif killed and not injured:
        status_string += '{} dead '.format(killed)
    elif injured and not killed:
        status_string += '{} injured '.format(injured)
    else:
        status_string += 'no injuries at this time '
    status_string += 'near {}, {}. '.format(city, state)
    #status_string += '{} {} '.format(incident_url, source_url)
    status_string += '{} {} '.format(
        SHORTENER.short(incident_url), SHORTENER.short(source_url))
    return status_string


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
                killed = int(incident[4].text)
                injured = int(incident[5].text)
                incident_url = incident[6].find('li', class_='0').find('a').attrs['href']
                incident_url = ''.join([base_url, incident_url])
                source_url = incident[6].find('li', class_='1').find('a').attrs['href']

                state_abbr = con.execute('SELECT abbr FROM states WHERE state = ?;', [state])
                state_abbr = state_abbr.fetchone()
                state = state_abbr[0]
                data = (date, state, city, address, killed, injured, incident_url, source_url)

                #con.execute('INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?)', data)
                query = 'SELECT twitterid FROM congress WHERE state = ? and role = "senator";'
                reps = con.execute(query, state_abbr)
                reps = reps.fetchall()
                reps = [''.join(['@', rep[0]]) for rep in reps]
                status_string = build_status(data)
                status_string += '{} {} '.format(reps[0], reps[1])
                print(status_string)
                input()
                api = connect_to_twitter()
                api.update_status(status_string)
                print('inserted', date, state, city)
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
