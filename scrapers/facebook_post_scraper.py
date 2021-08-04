from selenium import webdriver
from selenium.webdriver.remote.webdriver import _make_w3c_caps
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time
class Parameters:
    URLS = ["https://www.facebook.com/carta.dz"]
    MAX_RESULTS = 100
    HIDE_BROWSER = False
    USERNAME = "swileh.ly"
    PASSWORD = "zehzeh0809"


class PostScraper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = Parameters.HIDE_BROWSER
        self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe", options=chrome_options)
        self.driver.get("https://www.facebook.com/")
    
    def wait(self, xpath):
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    
    def login(self):
        self.driver.find_element_by_css_selector("input[name='email']").send_keys(Parameters.USERNAME)
        self.driver.find_element_by_css_selector("input[name='pass']").send_keys(Parameters.PASSWORD)
        self.driver.find_element_by_css_selector("button[name='login']").click()
        
    def go_to_page(self, url):
        self.driver.get(url)

    def get_account(self,post):
        pass
    
    def get_reactions(self,post):
        pass
    
    def get_date(self,post):
        pass
    
    def get_content(self,post):
        description = post.find_element_by_css_selector("div[data-ad-preview='message']")
        description.find_element_by_css_selector('div[role="button"]').click()
        return description.text

    def get_posts(self, urls, max_results):
        posts = []
        while len(posts) < max_results:
            for url in urls:
                print(url)
                self.go_to_page(url)
                new_posts = self.driver.find_elements_by_css_selector('div[role="feed"]')
                for post in new_posts:
                    if post in posts:
                        continue
                    posts += post
                return posts
            self.scroll()
        print(len(posts))
        return posts

    def scroll(self):
        SCROLL_PAUSE_TIME = 2
        last_height = 0
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                return
            if Parameters.MAX_SCROLL == 0:
                return
            Parameters.MAX_SCROLL -= 1
            last_height = new_height

def start_scraper(urls, max_results):
    scraper = PostScraper()
    scraper.login()
    posts = scraper.get_posts(urls, max_results)
    for post in posts:
        description = scraper.get_description(post)
        print(description)

if __name__ == '__main__':
    start_scraper(
        urls= Parameters.URLS,
        max_results= Parameters.MAX_RESULTS,
    )