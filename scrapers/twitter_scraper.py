from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import time
try:
    from youtube_scrapper import DBParameters 
    from twitter_db import RetweetDB, TweetsDB
except ImportError:
    from .youtube_scrapper import DBParameters 
    from .twitter_db import RetweetDB, TweetsDB

from datetime import datetime

class Parameters:
        KEY_WORDS = ["عيد","mehraz"]
        MAX_RESULTS = 100
        HIDE_BROWSER = False
        USERNAME = "ttt"
        PASSWORD = "tttt"

def normalize(num):
        num.replace(" ","")
        try:
                if 'K' in num or 'k' in num:
                        num = float(num.replace("K","").replace('k',"").replace(",","."))
                        num = num * (10** 3)
                        return int(num) 
                elif 'M' in num or 'm' in num:
                        num = float(num.replace("M","").replace("m","").replace(",","."))
                        num = num * (10** 6)
                        return int(num)
                elif 'B' in num or 'b' in num:
                        num = float(num.replace("B","").replace("b","").replace(",","."))
                        num = num * (10** 9)
                        return int(num)
                else:
                        return int(num)
        except:
                return num

def handle_none(value):
        if value == '' or value == None:
                return 0
        return value

def normalize_url(url):
    url_arr = url.split("/")
    if 'status' in url_arr:
        new_url = ''
        i = 1
        for item in url_arr:
            if i == 1:
                new_url += f'{item}'
            else:
                new_url += f'/{item}'
            i +=1
            if i == 7 :
                return new_url
    return 
        
    
def get_date(date):
        match = re.search(r'\d{4}-\d{2}-\d{2}', date)
        date = datetime.strptime(match.group(), "%Y-%m-%d").date()
        return date

def create_db():
        db = TweetsDB(
                host=DBParameters.HOST,
                user=DBParameters.USER,
                password=DBParameters.PASSWORD,
                db_name=DBParameters.DB_NAME,
        )
        db.create_table()
        return db

class TwitterScraper:
        
        def __init__(self):
            self.i = 100
            chrome_options = webdriver.ChromeOptions()
            chrome_options.headless = True
            if Parameters.HIDE_BROWSER:
                self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe", options=chrome_options)
            else:
                self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe")
        
        def login(self):
            self.driver.get("https://twitter.com/login")
            try:
                self.wait(xpath='.//input[@name="session[username_or_email]"]')
                username = self.driver.find_element_by_css_selector('input[name="session[username_or_email]"]')
                username.send_keys(Parameters.USERNAME)
                password = self.driver.find_element_by_css_selector('input[name="session[password]"]')
                password.send_keys(Parameters.PASSWORD)
                btn = self.driver.find_elements_by_css_selector('div[role="button"]')[0]
                btn.click()
            except TimeoutException:
                    self.login()
        
        def search(self, key_word):
                url = f'https://twitter.com/search?q={key_word}&src=typed_query'
                self.driver.get(url)
        
        def wait(self, xpath='.//div[@data-testid="like"]'):
                WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))

        def get_tweets(self, max_results):
                tweets = []
                replays = 0
                tweet_db = create_db()
                while True:
                        articles = self.driver.find_elements_by_xpath("//article")
                        urls = self.driver.find_elements_by_xpath("//article//div[2]/div[2]/div/div/div/div/a")
                        for i in range(len(articles)):
                                try:
                                        if urls[i] in tweets:
                                                continue
                                        else:
                                                try:
                                                        date  = articles[i].find_element_by_css_selector('time').get_attribute("datetime")
                                                        date = get_date(date) 
                                                        self.wait('.//div[@data-testid="reply"]')
                                                        reply = articles[i].find_element_by_css_selector('div[data-testid="reply"]').text
                                                        reply = handle_none(normalize(reply))
                                                        print(f"reply ==> {reply}")
                                                        retweet = articles[i].find_element_by_css_selector('div[data-testid="retweet"]').text
                                                        retweet = handle_none(normalize(retweet))
                                                        print(f"retweet ==> {retweet}")
                                                        likes = articles[i].find_element_by_css_selector('div[data-testid="like"]').text
                                                        likes = handle_none(normalize(likes))
                                                        print(f"likes ==> {likes}")
                                                        text  = articles[i].find_element_by_xpath('.//div[2]/div[2]/div[1]').text
                                                        print(f"text ==> {text}")
                                                        account  = articles[i].find_element_by_xpath('//div[@data-testid="tweet"]/div[2]/div[1]/div/div[1]/div[1]/div[1]/a/div/div[2]/div/span').text
                                                        print(f"account ==> {account}")
                                                        success, id  = tweet_db.insert_tweet_info(
                                                        tweet=text,
                                                        account=account,
                                                        likes=likes,
                                                        replays=reply,
                                                        retweets=retweet,
                                                        date=date,
                                                        )
                                                        replays += reply
                                                        if replays > max_results:
                                                                return tweets
                                                        tweets.append((urls[i].get_attribute("href"), id)) 
                                                except (StaleElementReferenceException, NoSuchElementException):
                                                        continue
                                except IndexError:
                                        break
                                        
                    
                        self.scroll()
            

        def scroll(self):            
            self.driver.execute_script(f"window.scrollTo(0,document.body.scrollHeight);")

        def create_db(self):
                retweets_db = RetweetDB(
                        host=DBParameters.HOST,
                        user=DBParameters.USER,
                        password=DBParameters.PASSWORD,
                        db_name=DBParameters.DB_NAME,        
                )
                retweets_db.create_table()
                return retweets_db

        def get_retweets(self, url, id, max_results):
                comments = []
                self.driver.get(url)
                self.wait()
                retweet_db  = self.create_db()
                retry = 11
                last_retweet = ''
                retweet = ""
                last_id = 0
                while True:
                        retweet = None
                        try:
                                self.wait('//div[@data-testid="tweet"]/div[2]/div[2]/div[2]')
                                retweets = self.driver.find_elements_by_xpath('//div[@data-testid="tweet"]/div[2]/div[2]/div[2]')
                        except TimeoutException:
                                break
                        for retweet in retweets:
                                if len(comments) > max_results:
                                        return comments
                                try:
                                        retweet = retweet.text
                                        retweet_added = retweet in comments
                                        if str(retweet) != '' and not retweet_added: 
                                                print(retweet)
                                                comments.append(retweet)
                                                retweet_db.insert_retweet(
                                                        tweet_id= id,
                                                        retweet= retweet
                                                )
                                except StaleElementReferenceException:
                                        continue
                        check_retweet = last_retweet == retweet
                        check_id = last_id == id
                        if check_retweet  & check_id :
                                retry -= 1
                        else:
                                last_retweet = retweet
                                last_id = id
                                retry = 5
                        if retry < 0:
                                break
                        self.scroll()
                        time.sleep(1)
                return comments




def get_retweets(scrapper, max_results, urls):
        comments = []
        tweets_urls = scrapper.get_tweets(max_results)
        if urls:
                tweets_urls += urls 
        for tweet_url, id in tweets_urls:
                retweet = None
                try:
                        retweets = scrapper.get_retweets(url=tweet_url, id=id, max_results=max_results)
                except TypeError:
                        continue
                if retweets :
                        for retweet in retweets:
                                if not (retweet in comments):
                                        comments += retweets
                                if len(comments) > max_results:
                                        return comments 
        return comments

def twitter_scraper(max_results, keywords, urls=[]):
        comments = []
        scrapper = TwitterScraper()
        print(keywords)
        scrapper.login()
        for key_word in keywords:
                scrapper.search(key_word)
                try:
                comments += get_retweets(scrapper, max_results, urls)
                except:
                        pass
        return comments
             


if __name__ == "__main__":
        c = twitter_scraper(
                keywords=Parameters.KEY_WORDS,
                max_results=Parameters.MAX_RESULTS,
        )   
        print(len(c))      

