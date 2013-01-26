"""
Written especially for downloading supreme court opinions as PDFs; parse the index pages, grab urls, then grab the pdfs that live at that url
"""
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import json
import os
import urllib2

high_level_indices = ["http://www.supremecourt.gov/opinions/11pdf/", "http://www.supremecourt.gov/opinions/10pdf/", "http://www.supremecourt.gov/opinions/09pdf/"]
mech = Browser()

def restoreLinksFromFile(filename):
  return json.loads(open(filename, "r").read())

def grabPage(url):
  if os.path.exists("indices/" + url.split("/")[-2] + ".html"):
    print "using cached index page"
    html = open("indices/" + url.split("/")[-2] + ".html", "r").read()
  else:
    print "no cache for " + url + ", dling"
    page = mech.open(url)
    html = page.read()
    open("indices/" + url.split("/")[-2] + ".html", "w").write(html)
  return html

def getPDF(name, url):
	escapedName = name.replace("/", "")
	if os.path.exists("pdfs/" + url.split("/")[-2] + "/" + escapedName):
		print "file exists!"
	else:
		if not os.path.exists("pdfs/" + url.split("/")[-2] + "/"):
			os.mkdir("pdfs/" + url.split("/")[-2] + "/")
		pdf = open("pdfs/" + url.split("/")[-2] + "/" + escapedName + ".pdf", "wb")
		req = urllib2.Request(url)
		opener = urllib2.build_opener()
		response = opener.open(req)
		result = pdf.write(response.read())
		print escapedName + " written successfully"

def getCasesFromIndex(html, url):
  soup = BeautifulSoup(html)
  secondCenter = soup.center.center

  links = []
  for link in secondCenter.findAll('a'):
    links.append([link.text, url + link.get('href')])
  return links

for index in high_level_indices:
  links = getCasesFromIndex(grabPage(index), index)
  for link in links:
  	getPDF(*link)

def getCaseText(caseName):
  #use docsplit from doccloud
  pass