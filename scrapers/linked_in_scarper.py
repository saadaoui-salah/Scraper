import requests
from bs4 import BeautifulSoup
import json
from youtube_scrapper import search_dict, find_value

client = requests.Session()

HOMEPAGE_URL = 'https://www.linkedin.com?allowUnsupportedBrowser=true'
LOGIN_URL = 'https://www.linkedin.com/uas/login-submit?allowUnsupportedBrowser=true'

html = client.get(HOMEPAGE_URL)
soup = BeautifulSoup(html.content, "html.parser")
csrf = soup.find_all("input")[0]['value']

def get_data(response):
    soup = BeautifulSoup(response.text,"lxml")
    needed_text = soup.find_all("code")
    #print(soup.prettify())
    data = json.loads(needed_text.text)
  
    return data
    
login_information = {
    'session_key':'*****@***.**',
    'session_password':'*****',
    'loginCsrfParam': csrf,
}

x = client.post(LOGIN_URL, data=login_information)
print(BeautifulSoup(x.text,"html").prettify())

x = client.get('https://www.linkedin.com/feed/update/urn:li:activity:6792829227583590400/?updateEntityUrn=urn%3Ali%3Afs_feedUpdate%3A%28V2%2Curn%3Ali%3Aactivity%3A6792829227583590400%29')

data = get_data(x) 
comments = search_dict(data, "comment")

