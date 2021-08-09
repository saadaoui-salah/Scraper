from selenium import webdriver
from selenium.webdriver.remote.webdriver import _make_w3c_caps
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
try:
    from instagrame_db import CommentDB, InstaDB
    from twitter_scraper import get_date
    from youtube_scrapper import DBParameters
except ImportError:
    from .instagrame_db import CommentDB, InstaDB
    from .twitter_scraper import get_date
    from .youtube_scrapper import DBParameters
import time


class Parameters:
    URLS = []
    KEY_WORDS = ["ronaldo"]
    MAX_RESULTS = 100
    MAX_TAGS = 10
    MAX_SCROLL = 5
    HIDE_BROWSER = False
    USERNAME = "saadaoui_salah_"
    PASSWORD = "saadaouisalah0809"

class InstaScraper:
        
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = Parameters.HIDE_BROWSER
        self.driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe", options=chrome_options)
        self.driver.get("https://www.instagram.com/")
    def wait(self, xpath):
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    def login(self):
        self.wait(xpath="//input[@name='password']")
        username_input = self.driver.find_element_by_css_selector("input[name='username']")
        password_input = self.driver.find_element_by_css_selector("input[name='password']")
        username_input.send_keys(Parameters.USERNAME)
        password_input.send_keys(Parameters.PASSWORD)
        submit = self.driver.find_element_by_css_selector("button[type='submit']")
        submit.click()
    def search(self, keywords):
        self.wait(xpath='//nav//input')
        search_input = self.driver.find_element_by_xpath('//nav//input')
        tags_url = []
        for key_word in keywords:
            search_input.clear()
            search_input.send_keys(key_word)
            self.wait(xpath="//section/nav/div[2]/div/div/div[2]/div[3]//a")
            tags = self.driver.find_elements_by_xpath('//section/nav/div[2]/div/div/div[2]/div[3]//a[starts-with(@href, "/explore/tags/")]')
            for tag in tags:
                url = tag.get_attribute("href")
                tags_url.append(url)
                if Parameters.MAX_TAGS is not None:
                    if Parameters.MAX_TAGS == 0:
                        break
                    Parameters.MAX_TAGS -= 1
        return tags_url
    
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
    
    def get_posts_url(self, keywords, max_results):
        max_results = max_results * 2
        tags_url = self.search(keywords)
        for tag_url in tags_url:
            self.driver.get(tag_url)
            self.wait("//article")
            self.scroll()
            posts = self.driver.find_element_by_xpath("//article")
            urls = posts.find_elements_by_xpath('//a[starts-with(@href, "/p/")]')
            for url in urls :
                url = url.get_attribute("href")
                max_results -= 1
                if max_results < 0 :
                    break
                Parameters.URLS.append(url)

    def go_to_post(self, url):
        self.driver.get(url)
        
    def get_account(self):
        self.wait("//header/div[2]//a")
        account = self.driver.find_element_by_xpath("//header/div[2]//a").text
        return account
    
    def get_date(self):
        self.wait(".//time")
        date = self.driver.find_element_by_css_selector("time").get_attribute("datetime")
        date = get_date(date)
        return date
    
    def get_description(self):
        self.wait(".//article/div[3]/div/ul[1]/div/li/div/div/div[2]/span")
        description = self.driver.find_element_by_xpath(".//article/div[3]/div/ul[1]/div/li/div/div/div[2]/span").text
        return description.replace("\n"," ")
    
    def get_content_and_likes(self):
        try:
            self.wait(".//article/div[2]//img")
            img_link = self.driver.find_element_by_xpath(".//article/div[2]//img").get_attribute("srcset")
            try:
                likes = self.driver.find_element_by_xpath(".//article//section[2]//a//span").text
                likes = int(likes.replace(" ",""))
                return img_link, likes
            except ValueError:
                likes = self.driver.find_element_by_xpath(".//article//section[2]/div/div[2]//a//span").text
                likes = int(likes.replace(" ",""))
                return img_link, likes

        except TimeoutException:
            try: 
                vues = self.driver.find_element_by_xpath(".//article//section[2]/div/span").click()
                likes = self.driver.find_element_by_xpath(".//article//section[2]/div/div//span").text
            except:
                likes = self.driver.find_element_by_xpath(".//article//section[2]//a//span").text
            likes = int(likes.replace(" ","").replace(",",""))
            video_link = self.driver.find_element_by_xpath(".//article//video").get_attribute("src")
            return  video_link, likes

    def get_comments(self, post_id):
        comments = []
        comment_db = CommentDB(
            host=DBParameters.HOST,
            user=DBParameters.USER,
            password=DBParameters.PASSWORD,
            db_name=DBParameters.DB_NAME
        )
        comment_db.create_table()
        while True:
            try:
                self.wait('//span[@aria-label="Charger d’autres commentaires"]')
                load_comments = self.driver.find_element_by_css_selector('span[aria-label="Charger d’autres commentaires"]')
                load_comments.click()
            except (TimeoutException, ElementClickInterceptedException):
                break
        while True:
            try:
                self.wait('//article/div[3]/div/ul/ul/li//button')
                load_comments = self.driver.find_element_by_xpath('//article/div[3]/div/ul/ul/li//button')
                text = self.driver.find_element_by_xpath('//article/div[3]/div/ul/ul/li//button//span').text
                text = text.lower()
                text_verification = "hide" in text or "masquer" in text
                if not text_verification: 
                    load_comments.click()
            except (TimeoutException, ElementClickInterceptedException):
                break
        self.wait(".//ul//ul")
        n_comments = 0
        new_comments = self.driver.find_elements_by_xpath(".//ul//ul//li/div/div/div[2]/span")
        for comment in new_comments:
            comment = comment.text
            print(f"comment ===============| {comment}")
            comment_db.insert_comments(post_id=post_id,comment=comment)
            n_comments += 1
            comments.append(comment)
        try :
            buttons = self.driver.find_elements_by_xpath("//ul//ul//li//li//button")
            for button in buttons:
                    button.click()
            self.wait(".//ul//ul//ul//div[2]/span")
            buttons = self.driver.find_elements_by_xpath("//ul//ul//li//li//button")
            sub_comments = self.driver.find_elements_by_xpath("//ul//ul//ul//div[2]/span")
            for comment in sub_comments:
                comment = comment.text
                print(f"comment ===============| {comment}")
                comment_db.insert_comments(post_id=post_id,comment=comment)
                n_comments += 1
                comments.append(comment)
        except TimeoutException:
            pass
        return n_comments, comments 

posts_db = InstaDB(
        host=DBParameters.HOST,
        user=DBParameters.USER,
        password=DBParameters.PASSWORD,
        db_name=DBParameters.DB_NAME
    )
posts_db.create_table()

def insta_scraper(max_results, keywords=None, urls=None):
    scraper = InstaScraper()
    print(keywords)
    comments = []
    scraper.login()
    if keywords:
        scraper.get_posts_url(keywords, max_results)
    if urls:
        Parameters.URLS += urls
    for url in Parameters.URLS:
        scraper.go_to_post(url)
        account = scraper.get_account()
        print(f"account ==> {account}")
        date = scraper.get_date()
        print(f"date ==> {date}")
        try:
            content_link, likes = scraper.get_content_and_likes()
        except:
            content_link = 'https://'
            likes = 0
        print(f"content_link ==> {content_link}")
        print(f"likes ==> {likes}")
        description = scraper.get_description()
        print(f"description ==> {description}")
        id = posts_db.insert_post_info(
            account=account,
            published_date=date,
            description=description,
            likes=likes,
            content_link=content_link,
            n_comments=0
        )
        try:
            n_comments, new_comments = scraper.get_comments(id)
            posts_db.update_n_comments(n_comments, id)    
            comments += new_comments
        except : 
            pass
    return comments
    
if __name__ == "__main__":
    c = insta_scraper(
        urls=Parameters.URLS,
        keywords=Parameters.KEY_WORDS,
        max_results=Parameters.MAX_RESULTS
    )
    print(f"num comments ====> {len(c)}")
