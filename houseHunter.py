import requests
import pickle
import smtplib
from string import Template
from BeautifulSoup import BeautifulSoup
import sys, os
import datetime
import time
import traceback


class Hunter():
    sleepTime = 900
    pickleFileName = 'SavedListings.pkl'
    currentListings = None
    listingsFound = None
    utahrealestateUrl = r'http://www.utahrealestate.com/search/public.search?accuracy=5&geocoded={0}&box=%257B%2522north%2522%253A40.71271490000001%252C%2522south%2522%253A40.51886100000001%252C%2522east%2522%253A-111.520936%252C%2522west%2522%253A-111.871398%257D&htype=zip&lat=40.6210656&lng=-111.81713739999998&geolocation=Salt+Lake+City%2C+UT+{0}&type=1&listprice1=&listprice2={1}&proptype=1&state=ut&tot_bed1=&tot_bath1=&tot_sqf1={2}&dim_acres1={3}&yearblt1=&cap_garage1=&style=&o_style=4&opens=&accessibility=&o_accessibility=32&page={4}'
    emailBody = Template("""
        <a href='https://maps.google.com/?q=${address}, ${city}, UT ${zip}'>${address}, ${city}, UT ${zip}</a>
        <br>
        ${stats}
        <br>
        ${priceStr} | ${ppsqft} per square foot
        <br>
        ${acres} acres
        <br>
        <a href='http://www.utahrealestate.com/report/public.single.report/report/detailed/listno/${mls}/scroll_to/${mls}'>
            <img src='${photoUrl}'>
        </a>
        <br>
        This email brought to you by your amazing husband. :)
        <br>
        houseHunter.py Auto-generated
    """)

    # constructor params
    email = None
    password = None
    zipCodes = []
    maxPrice = None
    minSqFt = None
    minLotSize = None

    def __init__(self, email, password, zips, maxPrice, minSqFt, minLotSize):
        self.email = email
        self.password = password
        self.zipCodes = zips.split(',')
        self.maxPrice = maxPrice
        self.minSqFt = minSqFt
        self.minLotSize = minLotSize

    def startSearch(self):
        statusSearches = 0
        totalSearches = 0
        while True:
            totalSearches = totalSearches + 1
            statusSearches = statusSearches + 1
            try:
                print 'search #{}'.format(totalSearches)
                self.search()
            except:
                print 'Error with search function!'

                try:
                    tb = sys.exc_info()[2]
                    pymsg = traceback.format_tb(tb)[0]
                
                    if sys.exc_type:
                        pymsg = pymsg + "\n" + str(sys.exc_type) + ": " + str(sys.exc_value)
                
                    print pymsg
                except:
                    print 'Problem getting traceback object'
            finally:
                if statusSearches == 4:
                    self.sendEmail('houseHunter.py is still running', 'Let not your heart be troubled. I\'m working hard to find you a home.')
                    print 'status email sent'
                    statusSearches = 0
                print 'sleeping for {} minutes...'.format(self.sleepTime/60)
                time.sleep(self.sleepTime)

    def search(self):
        self.currentListings = self.getSavedListings()
        self.listingsFound = []
        
        for zip in self.zipCodes:
            print zip

            # this is required to make their site return the correct data
            s = requests.Session()
            s.get(r'http://www.utahrealestate.com/index/public.index')

            page = 1
            while True:
                url = self.utahrealestateUrl.format(zip, self.maxPrice, self.minSqFt, self.minLotSize, page)
                r = s.get(url)

                listings = self.getListingsFromHTML(r.text)
                if len(listings) == 0:
                    break

                for l in listings:
                    self.listingsFound.append(l.mls)
                    if l.mls in self.currentListings.keys():
                        # check for price change
                        current = self.currentListings[l.mls]
                        if not l.price == current.price:
                            self.sendProperty(l, 'Price change from {} to {}'.format(current.price, l.price))
                            self.currentListings[l.mls] = l
                            print 'Price change for: {}'.format(l.mls)
                    else:
                        self.sendProperty(l, None)
                        self.currentListings[l.mls] = l
                        print 'New property found: {}'.format(l.mls)
                page = page + 1
            s.close()

        self.checkForOffTheMarkets()

        with open(self.pickleFileName, 'w') as file:
            pickle.dump(self.currentListings, file)

    def getSavedListings(self):
        if not os.path.exists(self.pickleFileName):
            return {}
        else:
            with open(self.pickleFileName, 'rb') as file:
                return pickle.load(file)

    def getListingsFromHTML(self, htmlText):
        soup = BeautifulSoup(htmlText)
        listings = []
        for listTable in soup.findAll('table', {'class': 'public-detail-quickview'}):
            list = Listing()
            list.mls = listTable.find('p', {'class': 'public-detail-overview-b'}).contents[2].string.strip()
            list.priceStr = listTable.h2.span.string
            list.price = int(list.priceStr[1:].replace(',', ''))
            list.photoUrl = listTable.img['src']
            if listTable.h2.i:
                list.address = listTable.h2.i.string.replace('  ', ' ')
                cityZip = listTable.h2.i.nextSibling.string.split(', ')
                list.city = cityZip[1]
                list.zip = cityZip[2].strip()[-5:]
            else:
                addressParts = listTable.h2.span.nextSibling.string.strip().split(', ')
                list.address = addressParts[0].replace('  ', ' ')
                list.city = addressParts[1]
                list.zip = addressParts[2][-5:]
            list.sqft = int(listTable.find('p', {'class': 'public-detail-overview'}).string.strip()[-12:-8])
            list.ppsqft = list.price / list.sqft
            list.acres = float(listTable.find('p', {'class': 'public-detail-overview-b'}).contents[-1].strip())
            list.stats = listTable.find('p', {'class': 'public-detail-overview'}).string.strip()

            listings.append(list)

        return listings

    def sendProperty(self, listing, additionalText=None):
        if additionalText is None:
            body = self.emailBody.substitute(listing.__dict__)
        else:
            body = '<h3>{}</h3>'.format(additionalText) + self.emailBody.substitute(listing.__dict__)

        subject = '{} | {} sf | {}, {} {}'.format(listing.priceStr, listing.sqft, listing.address, listing.city, listing.zip)
        self.sendEmail(subject, body)

    def sendEmail(self, sub, body):
        headers = [
            "from: " + email,
            "subject: " + sub,
            "to: " + email,
            "mime-version: 1.0",
            "content-type: text/html"
        ]
        headers = "\r\n".join(headers)

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(self.email, self.password)
        server.sendmail(email, email, headers + '\r\n\r\n' + body)

    def checkForOffTheMarkets(self):
        for mls in self.currentListings.keys():
            if mls not in self.listingsFound:
                listing = self.currentListings[mls]
                try:
                    timeOnMarket = (datetime.datetime.now() - datetime.datetime.fromtimestamp(listing.foundDate)).days
                except:
                    timeOnMarket = '???'
                self.sendProperty(listing, 'Listing Off Market in {} days!!!'.format(timeOnMarket))
                del self.currentListings[mls]


class Listing():
    mls = ''
    price = 0
    priceStr = ''
    photoUrl = ''
    address = ''
    city = ''
    zip = ''
    sqft = 0
    ppsqft = 0
    acres = 0.0
    foundDate = None
    stats = ''

    def __init__(self):
        self.foundDate = time.time()

if __name__ == '__main__':
    def getParam(i, prompt):
        if len(sys.argv) > i and len(sys.argv[i]) > 0:
            return sys.argv[i]
        else:
            return raw_input('{}: '.format(prompt))

    email = getParam(1, 'gmail account email address')
    password = getParam(2, 'password')
    zips = getParam(3, 'zip codes, separated by commas (i.e. 84121,84092,84105)')
    maxPrice = getParam(4, 'max price (i.e. 300000)')
    minSqFt = getParam(5, 'min square footage (i.e. 2200)')
    minLotSize = getParam(6, 'min lot size in acres (i.e. .20)')

    Hunter(email, password, zips, maxPrice, minSqFt, minLotSize).startSearch()