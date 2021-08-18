from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import requests
from datetime import datetime
try:
    from facebook_db import FacbookPostDB
    from youtube_scrapper import DBParameters
except ImportError:
    from .facebook_db import FacbookPostDB
    from .youtube_scrapper import DBParameters


class Parameters:
    URLS = ["https://www.facebook.com/carta.dz"]
    MAX_RESULTS = 5
    HIDE_BROWSER = False

def get_proxy():
    r = requests.get("http://pubproxy.com/api/proxy")
    data = r.json()
    return data['data'][0]['ipPort']

class PostScraper:
    def __init__(self):
        proxy = get_proxy()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = Parameters.HIDE_BROWSER
        webdriver.DesiredCapabilities.CHROME['proxy']={
            "httpProxy":proxy,
            "ftpProxy":proxy,
            "sslProxy":proxy,
            
            "proxyType":"MANUAL",
            
        }
        self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe", options=chrome_options)
        self.last_height = 0
        self.toolbar_data = {
            'like':0,
            'love':0,
            'care':0,
            'haha':0,
            'wow':0,
            'sad':0,
            'angry':0,
        }
    def wait(self, xpath):
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))

    def skip_login_tab(self):
        self.driver.find_element_by_css_selector("a[data-nocookies='1']").click()

    def go_to_page(self, url):
        self.driver.get(url)
        post = self.driver.find_element_by_css_selector('div[data-visualcompletion="ignore-dynamic"]')
        return post 

    def get_account(self):
        account = self.driver.find_element_by_css_selector('meta[property="og:title"]').get_attribute("content")
        return account

    def get_reactions(self,post):
        reactions = post.find_element_by_css_selector('span[role="toolbar"]')
        reactions = reactions.find_elements_by_css_selector('a[rel="dialog"]')
        for reaction in reactions:
            reaction_data = reaction.get_attribute('aria-label')
            try:
                reaction_data = reaction_data.split(' ')
                reaction_name = reaction_data[1].lower() 
            except :
                continue
            if reaction_name == "j’aime" or reaction_name == 'like':
                self.toolbar_data['like'] = int(reaction_data[0])
            if reaction_name == "j’adore" or reaction_name == 'love':
                self.toolbar_data['love'] = int(reaction_data[0])
            if reaction_name == "solidaire" or reaction_name == 'care':
                self.toolbar_data['care'] = int(reaction_data[0])
            if reaction_name == "haha": 
                self.toolbar_data[reaction_name] = int(reaction_data[0])
            if reaction_name == "wouah" or reaction_name == 'wow': 
                self.toolbar_data['wow'] = int(reaction_data[0])
            if reaction_name == "triste" or reaction_name == 'sad':
                self.toolbar_data['sad'] = int(reaction_data[0])
            if reaction_name == "grrr" or reaction_name == 'angry':
                self.toolbar_data['angry'] = int(reaction_data[0])
        return self.toolbar_data

    def get_date(self,post):
        timstamp = int(post.find_element_by_tag_name('abbr').get_attribute("data-utime"))
        date = datetime.fromtimestamp(timstamp)
        return date
    
    def get_description(self,post):
        text = '' 
        try:
            post.find_element_by_class_name("see_more_link").click()
        except :
            pass
        lines = post.find_elements(By.XPATH, ".//div[@data-testid='post_message']//p")
        for line in lines:
            text += ' ' + line.get_attribute("textContent")
        return text

    def get_num_form_text(self, text):
        text = text.split(' ')
        return text[0]
    def connect_to_db(self):
        db = FacbookPostDB(
            host = DBParameters.HOST,
            user = DBParameters.USER,
            password = DBParameters.PASSWORD,
            db_name = DBParameters.DB_NAME,
            )
        db.create_table()
        return db

    def get_commments_num(self, post):
        try:
            attr = '{"tn":"O"}'
            text = post.find_element_by_css_selector(f"a[data-ft='{attr}']").text
            return self.get_num_form_text(text)
        except :
            return 0
    def get_shares_num(self, post):
        try:
            text = post.find_element_by_css_selector('a[data-testid="UFI2SharesCount/root"]').text
            return self.get_num_form_text(text)
        except :
            return 0

    def get_posts(self, url, max_results):
        new_posts = []
        print(f"Go to {url}...")
        self.go_to_page(url)
        while True:
            new_posts = self.driver.find_elements_by_css_selector('div[data-insertion-position]')
            if len(new_posts) >= max_results:
                print(f"\t{len(new_posts)} Posts Scrapped")        
                return new_posts[0:max_results+1]
            end  = self.scroll()
            if end:
                break
        print(f"\t{len(new_posts)} Posts Scrapped")
        return new_posts

    def scroll(self):
        SCROLL_PAUSE_TIME = 2
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        if new_height == self.last_height:
            return True
        self.last_height = new_height
        return False

def start_scraper(urls, max_results):
    scraper = PostScraper()
    for url in urls:
        posts = scraper.get_posts(url, max_results)
        try:
            scraper.skip_login_tab()
        except: 
            pass
        page_name = scraper.get_account()
        print(f"\Page Name: '{page_name}'")
        for post in posts:
            description = scraper.get_description(post)
            try:
                print(f"\tDescription: '{description}'")
            except OSError:
                print("[WARNING]: Can't print description")
            date = scraper.get_date(post)
            print(f"\tDate: '{date.month}'")
            try:
                scraper.get_reactions(post)
                print(f"\treactions: '{scraper.toolbar_data}'")
            except :
                pass
            comments_num = scraper.get_commments_num(post)
            print(f"\tComments Number : {comments_num}")
            shares_num = scraper.get_shares_num(post)
            print(f"\tShares Number : {shares_num}")
            
            db = scraper.connect_to_db()
            db.insert_post_info(
                page_name=page_name,
                description=description,
                reactions=scraper.toolbar_data,
                comments=comments_num,
                shares=shares_num,
                date=date 
            )

            scraper.toolbar_data = {
                'like':0,
                'love':0,
                'care':0,
                'haha':0,
                'wow':0,
                'sad':0,
                'angry':0,
            } 
if __name__ == '__main__':
    start_scraper(
        urls= Parameters.URLS,
        max_results= Parameters.MAX_RESULTS,
    )