house-hunter
===========

A python script to scrape utahrealestate.com since their search is horrible.


Instructions for use for my non-programmer friends
==================================================

You'll want to open up houseHunter.py and edit the list of zip codes that it searches for as well as the max price, min lot size and min square footage.

This script requires that you have [Python 2.*](http://python.org/download/) installed on your computer.

It also requires these third party python libraries:
- requests
- BeautifulSoup


To run the script, you need to open your command window and browser to the folder that the script is in and run: 
```
houseHunter.py <your gmail address> <your gmail password>
```

It will then start a process that crawls the utahrealestate.com website every 15 minutes and sends you an email whenever it finds a new house. It stores a list of the houses that it has found in a .pkl file in the same directory as the script. That way if you need to stop it and restart it, it won't send you all of the houses again. It will also send you an email if a house has changed it's price or has gone off of the market.

This is something that I've just thrown together and comes with no guarantees. However, it's working well for us and has saved us lots of time searching on our own.