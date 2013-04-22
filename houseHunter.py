import requests
import pickle
import smtplib
from string import Template
from BeautifulSoup import BeautifulSoup
import json
import traceback
import sys
import datetime
import time


zipCodes = [
    '84093',
    '84121',
    '84117',
    '84124',
    '84106',
    '84109',
    '84107'
]

baseURL = r'http://www.utahrealestate.com/search/public.search?geocoded={0}&htype=zip&state=ut&type=1&listprice2=450000&proptype=1&tot_sqf1=2500&dim_acres1=.20&view=list&page={1}'
emailBody = Template("""
${stats}
<br>
${acres} acres
<br>
<a href='https://maps.google.com/?q=${add}'>${add}</a>
<br>
${price} | ${ppsqft} per square foot
<br>
${photoTag}
<br>
http://www.utahrealestate.com/report/public.single.report/report/detailed/listno/${mls}/scroll_to/${mls}
<br>
This email brought to you by your amazing husband. :)
<br>
houseHunter.py Auto-generated
""")

fileName = 'houses.pkl'
onMarket = 'onMarket.pkl'
onmarket = None
currentListings = []
if sys.argv[0]:
    email = sys.argv[1]
else:
    email = raw_input('gmail account email address: ')
if sys.argv[1]:
    password = sys.argv[2]
else:
    password = raw_input('password: ')

no_more = False

sleepTime = 900

session = requests.Session()
session.get(baseURL)


def searchPage(txt):
    global no_more, onmarket, currentListings

    soup = BeautifulSoup(txt)

    listings = soup.findAll('table', {"class": 'public-detail-quickview'})
    if len(listings) == 0:
        print 'No more properties!!!'
        no_more = True
    else:
        for listing in listings:
            props = {}
            props['price'] = listing.h2.span.string
            props['photoTag'] = "'{0}'".format(listing.img)
            props['mls'] = listing.find('p', {'class': 'public-detail-overview-b'}).contents[2].string.strip()
            props['add'] = listing.h2.span.nextSibling.string.strip()
            zip = props['add'][-5:]
            props['stats'] = listing.find('p', {'class': 'public-detail-overview'}).string.strip()
            props['sqft'] = props['stats'][-12:-8]
            props['ppsqft'] = int(props['price'][1:].replace(',', '')) / int(props['sqft'])
            props['acres'] = listing.find('p', {'class': 'public-detail-overview-b'}).contents[-1].strip()
            if zip in zipCodes:
                currentListings.append(props['mls'])
                if props['mls'] in onmarket.keys():
                    # check for price change...
                    if not props['price'] == json.loads(onmarket[props['mls']])['price']:
                        sendProperty(props, 'Price changed from {0} to {1}'.format(
                            json.loads(onmarket[props['mls']])['price'], props['price']))
                        onmarket[props['mls']] = json.dumps(props)
                else:
                    sendProperty(props, None)
                    props['foundDate'] = time.time()
                    onmarket[props['mls']] = json.dumps(props)
                    print props['mls']


def sendProperty(props, additionalText):
    add = email
    if additionalText is not None:
        body = '<h3>{0}</h3>'.format(additionalText) + emailBody.substitute(props)
    else:
        body = emailBody.substitute(props)

    headers = [
        "from: " + add,
        "subject: " + '{0} | {1}'.format(props['price'], props['add']),
        "to: " + add,
        "mime-version: 1.0",
        "content-type: text/html"
    ]
    headers = "\r\n".join(headers)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(add, password)
    server.sendmail(add, add, headers + '\r\n\r\n' + body)


def checkForOffTheMarkets():
    global currentListings, onmarket
    print 'checking for off the markets...'
    for mls in onmarket.keys():
        if mls not in currentListings:
            prop = json.loads(onmarket[mls])
            timeOnMarket = datetime.datetime.now() - datetime.datetime.fromtimestamp(prop['foundDate'])
            sendProperty(prop, 'Listing Off Market in {0} days!!!'.format(timeOnMarket.days))
            del onmarket[mls]


def search():
    global no_more, onmarket, onMarket
    no_more = False
    try:
        print 'opening pickle file'
        pkl_file = open(onMarket, 'rb')
        onmarket = pickle.load(pkl_file)
        pkl_file.close()
    except:
        print 'no pickle file found'
        onmarket = {}

    print 'searching...'
    pg = 1
    while not no_more:
        url = baseURL.format(zip, pg)
        r = session.get(url)

        searchPage(r.text)

        pg = pg + 1

    checkForOffTheMarkets()

    print 'saving pickle file'
    output = open(onMarket, 'wb')
    pickle.dump(onmarket, output)
    output.close()


while True:
    try:
        search()
    except:
        print 'ERROR with search function!'
        try:
            tb = sys.exc_info()[2]
            pymsg = traceback.format_tb(tb)[0]
        
            if sys.exc_type:
                pymsg = pymsg + "\n" + str(sys.exc_type) + ": " + str(sys.exc_value)
        
            print pymsg
        except:
            print 'Problem getting traceback object'
    finally:
        print 'sleeping for {0} minutes...'.format(sleepTime/60)
        time.sleep(sleepTime)
