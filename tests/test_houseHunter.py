import unittest, os, sys, pickle
from mock import patch, Mock
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')
import houseHunter

email = 'test@test.com'
password = 'password'
zips = '84121,84117,84123'
zipCodes = ['84121', '84117', '84123']
maxPrice = '470000'
minSqFt = '2200'
minLotSize = '.10'

testPickleFileName = 'test.pkl'
value = 'blah'


class initTests(unittest.TestCase):
    def tearDown(self):
        self.to = None

    def test_mixinParams(self):
        self.to = houseHunter.Hunter(email, password, zips, maxPrice, minSqFt, minLotSize)

        self.assertEqual(self.to.email, email)
        self.assertEqual(self.to.password, password)
        self.assertEqual(self.to.zipCodes, zipCodes)
        self.assertEqual(self.to.maxPrice, maxPrice)
        self.assertEqual(self.to.minSqFt, minSqFt)
        self.assertEqual(self.to.minLotSize, minLotSize)


class getSavedListings(unittest.TestCase):
    def setUp(self):
        self.to = houseHunter.Hunter(email, password, zips, maxPrice, minSqFt, minLotSize)
        self.to.pickleFileName = testPickleFileName
 
    def tearDown(self):
        self.to = None
        if os.path.exists(testPickleFileName):
            os.remove(testPickleFileName)
         
    def test_returnsEmptyDictIfNoFile(self):
        if os.path.exists(self.to.pickleFileName):
            os.remove(self.to.pickleFileName)
 
        self.assertEqual(self.to.getSavedListings(), {})
 
    def test_returnsPickleContentsIfFileExists(self):
        if not os.path.exists(self.to.pickleFileName):
            open(self.to.pickleFileName, 'w')
        with patch.object(pickle, 'load', return_value=value):
            self.assertEqual(self.to.getSavedListings(), value)
  
# this test causes an infinite loop with rerun
# class search(unittest.TestCase):
#     def test_setsCurrentListings(self):
#         self.to = houseHunter.Hunter(email, password, zips, maxPrice, minSqFt, minLotSize)
#         self.to.pickleFileName = testPickleFileName
  
#         with patch.object(houseHunter.Hunter, 'getSavedListings', return_value=value):
#             class Object(object):
#                 pass
#             r = Object()
#             r.text = 'blah'
#             with patch.object(requests.Session, 'get', return_value=r):
#                 self.to.search()
#                 self.assertEqual(self.to.currentListings, value)
  
#         self.to = None
  
  
class getUtahRealEstateListingsFromHTML(unittest.TestCase):
    def setUp(self):
        self.to = houseHunter.Hunter(email, password, zips, maxPrice, minSqFt, minLotSize)
        with open('utahRealEstateListingPage.html', 'r') as file:
            listingPageText = file.read()
 
        self.listings = self.to.getUtahRealEstateListingsFromHTML(listingPageText)
     
    def tearDown(self):
        self.to = None
         
    def test_getCorrectNumberOfListings(self):
        self.assertEqual(len(self.listings), 2)
 
    def test_getCorrectProps(self):
        listing = self.listings[0]
 
        self.assertEqual(listing.mls, '1142734')
        self.assertEqual(listing.price, 180000)
        self.assertEqual(listing.photoUrl, "http://photo.wfrmls.com/280x220/1142734.jpg")
        self.assertEqual(listing.address, '7927 S Titian Way')
        self.assertEqual(listing.city, 'Cottonwood Heights')
        self.assertEqual(listing.zip, '84121')
        self.assertEqual(listing.sqft, 2573)
        self.assertEqual(listing.ppsqft, 69)
        self.assertEqual(listing.acres, 0.53)
        self.assertEqual(listing.stats, '2 Bedrooms | 2.00 Bathrooms | 2573 sq. ft.')
        self.assertEqual(listing.priceStr, '$180,000')
        self.assertEqual(listing.url, r'http://www.utahrealestate.com/report/public.single.report/report/detailed/listno/1142734/scroll_to/1142734')
 
    def test_streetAddNotAvailable(self):
        listing = self.listings[1]
 
        self.assertEqual(listing.address, 'Street Address Not Available')
        self.assertEqual(listing.city, 'Holladay')
        self.assertEqual(listing.zip, '84121')
        
responseMock = Mock(spec=requests.Response)
class getKSLListingsFromHTML(unittest.TestCase):
    @patch.object(requests.Session, 'get', return_value=responseMock)
    def setUp(self, mock):
        self.to = houseHunter.Hunter(email, password, zips, maxPrice, minSqFt, minLotSize)
        with open('kslListingPage.html', 'r') as file:
            listingPageText = file.read()
         
        with open('kslAdPage.html', 'r') as file:
            responseMock.text = file.read()
        self.listings = self.to.getKSLListingsFromHTML(listingPageText)
     
    def test_getCorrectNumberOfListings(self):
        self.assertEqual(len(self.listings), 15)
         
    def test_getCorrectProps(self):
        listing = self.listings[5]
          
        self.maxDiff = None
  
        self.assertEqual(listing.mls, 'ksl-24988600')
        self.assertEqual(listing.price, 465000)
        self.assertEqual(listing.photoUrl, r"http://img.ksl.com/c/2983/298399/29839989.jpg?filter=marketplace/general_listing")
        self.assertEqual(listing.url, u'http://www.ksl.com/index.php?nid=475&ad=24988600&cat=&lpid=3&type=1&city=&zipcode=84121&distance=&sale=1&start=0&end=&state=UT&sort=&keyword=&sqftstart=&sqftend=&acresstart=&acresend=&bedrooms=&bathrooms=&sellertype=&ad_cid=6')
        self.assertEqual(listing.address, '7710 S Quicksilver Dr')
        self.assertEqual(listing.city, 'Cottonwood Heights')
        self.assertEqual(listing.zip, '84121')
        self.assertEqual(listing.sqft, 4831)
        self.assertEqual(listing.ppsqft, 96)
        self.assertEqual(listing.acres, 0.28)
        self.assertEqual(listing.stats, 'Beds: 4 | Baths: 3.50 | Sq Ft: 4831')
        self.assertEqual(listing.priceStr, '$465,000')
        