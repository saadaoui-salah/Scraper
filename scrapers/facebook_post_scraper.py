from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from datetime import datetime
try:
    from facebook_db import FacbookPostDB
    from youtube_scrapper import DBParameters
except ImportError:
    from .facebook_db import FacbookPostDB
    from .youtube_scrapper import DBParameters


class Parameters:
    URLS = ["https://www.facebook.com/carta.dz"]
    MAX_RESULTS = 20
    HIDE_BROWSER = False


class PostScraper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = Parameters.HIDE_BROWSER
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
        date = post.find_element_by_class_name('timestampContent').text
        date = datetime.strptime(date,"%d %M %Y")
        return date
    
    def get_description(self,post):
        text = '' 
        try:
            post.find_element_by_class_name("see_more_link").click()
        except :
            print("error")
            pass
        element = post.find_element_by_css_selector("div[class='text_exposed_root']")
        lines = element.find_elements_by_tag_name("p")
        for line in lines:
            text += ' ' + line.text
        return text

    def get_num_form_text(self, text):
        text = text.split(' ')
        return text[0]


    def get_commments_num(self, post):
        attr = "{'tn:'O'}"
        text = post.find_element_by_css_selector(f"a[data-ft='{attr}']").text
        return self.get_num_form_text(text)

    def get_shares_num(self, post):
        text = post.find_element_by_css_selector('a[data-testid="UFI2SharesCount/root"]').text
        return self.get_num_form_text(text)

    def get_posts(self, urls, max_results):
        posts = []
        for url in urls:
            print(f"Go to {url}...")
            self.go_to_page(url)
            while len(posts) < max_results:
                new_posts = self.driver.find_elements_by_css_selector('div[data-insertion-position]')
                for post in new_posts:
                    if len(posts) >= max_results:
                        print(f"\t{len(posts)} Posts Scrapped")        
                        return posts
                    if post in posts:
                        pass
                    else : 
                        posts.append(post)
                end  = self.scroll()
                if end:
                    break
        print(f"\t{len(posts)} Posts Scrapped")
        return posts

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
    posts = scraper.get_posts(urls, max_results)
    try:
        scraper.skip_login_tab()
    except: 
        pass
    account = scraper.get_account()
    print(f"\Page Name: '{account}'")
    for post in posts:
        print(post)
        description = scraper.get_description(post)
        print(f"\tDescription: '{description}'")
        #date = scraper.get_date(post)
        #print(f"\tDate: '{date}'")
        scraper.get_reactions(post)
        print(f"\treactions: '{scraper.toolbar_data}'")
        scraper.toolbar_data = {
            'like':0,
            'love':0,
            'care':0,
            'haha':0,
            'wow':0,
            'sad':0,
            'angry':0,
        } 
        comments_num = scraper.get_commments_num(post)
        print(f"\tComments Number : {comments_num}")
        shares_num = scraper.get_commments_num(post)
        print(f"\tShares Number : {shares_num}")
if __name__ == '__main__':
    start_scraper(
        urls= Parameters.URLS,
        max_results= Parameters.MAX_RESULTS,
    )