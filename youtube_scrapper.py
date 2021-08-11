import json
import time
import requests
from datetime import datetime
from youtube_search import YoutubeSearch
try:
    from youtube_db import VideosDB, CommentDB
except :
    from .youtube_db import VideosDB, CommentDB

import re

class Parameters:
    URLS = []
    MAX_COMMENTS = 20

class SearchParameters:
    KEY_WORDS = ['رمضان']
    MAX_RESULTS = 10

class DBParameters():
    HOST = 'localhost'
    USER = "root"
    PASSWORD = "Saadaouisalah0809"
    DB_NAME = "youtube"


YOUTUBE_COMMENTS_AJAX_URL = 'https://www.youtube.com/comment_service_ajax'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

def normalize(num):
    if 'K' in num or 'ألف' in num :
        num = num.replace("K","").replace("ألف","").replace("ًا","")
        num = float(num.replace(",","."))
        num = num * (10** 3)
        return int(num) 
    elif 'M' in num or 'مليون' in num :
        num = num.replace("M","").replace("مليون","")
        num = float(num.replace(",","."))
        num = num * (10** 6)
        return int(num)
    elif 'B' in num or 'مليار' in num :
        num = num.replace("B","").replace("مليار","")
        num = float(num.replace(",","."))
        num = num * (10** 9)
        return int(num)
    else:
        return int(num.replace(",",""))

def find_value(html, key, num_chars=2, separator='"'):
    pos_begin = html.find(key) + len(key) + num_chars
    pos_end = html.find(separator, pos_begin)
    return html[pos_begin: pos_end]


def ajax_request(session, url, params=None, data=None, headers=None, retries=5, sleep=20):
    for _ in range(retries):
        response = session.post(url, params=params, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            print(f"STATUS CODE {response.status_code}")
        else:
            time.sleep(sleep)

def insert_into_youtube_vidoes(chanel,subscribes,link,title,description,likes,dislikes,views,date):
    yt = VideosDB(
        host=DBParameters.HOST,
        user=DBParameters.USER,
        password=DBParameters.PASSWORD,
        db_name=DBParameters.DB_NAME,
    )
    yt.create_table()
    id = yt.insert_video_info(chanel,subscribes,link,title,description,likes,dislikes,views,date)
    return id

def insert_into_youtube_comments(video_id,comment):
    comment_obj = CommentDB(
        host=DBParameters.HOST,
        user=DBParameters.USER,
        password=DBParameters.PASSWORD,
        db_name=DBParameters.DB_NAME,
    )
    comment_obj.create_table()
    id = comment_obj.insert_comments(video_id,comment)
    return id

def search_dict(partial, search_key):
    stack = [partial]

    while stack:
        current_item = stack.pop()
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)

def get_chanel(data):
    for d in search_dict(data,"videoOwnerRenderer"):
        chanel = d['title']['runs'][0]['text']
        return chanel

def get_subscribers(data):
    for d in search_dict(data,"videoOwnerRenderer"):
        subscribers = d['subscriberCountText']['accessibility']['accessibilityData']['label']
        subscribers = subscribers.replace("مشترك","")
        subscribers = subscribers.replace("مشتركًا","")
        subscribers = subscribers.replace("subscribers","")
        subscribers = normalize(subscribers)
        return subscribers

def get_title_and_views(data):
    for d in search_dict(data,"videoPrimaryInfoRenderer"):
        title = d['title']['runs'][0]['text']
        views = int(d['viewCount']['videoViewCountRenderer']['viewCount']['simpleText'].replace(",","").split(" ")[0])
        return title,views

def get_likes_and_dislikes(data):
    for d in search_dict(data,"sentimentBarRenderer"):
        sentiments  = d['tooltip'].replace(" ","").split('/')
        likes = int(sentiments[1].replace(',',''))
        dislikes = int(sentiments[0].replace(',',''))
        return likes, dislikes

def get_date(data):
    for d in search_dict(data,"dateText"):
        text = str(d['simpleText'].replace("\u200f",""))
        try:
            match = re.search(r'\d{2}/\d{2}/\d{4}', text)
            date = datetime.strptime(match.group(), "%d/%m/%Y").date()
            return date
        except Exception:
            return datetime.now() 

def get_description(data):
    for d in search_dict(data,"description"):
        description = " "
        for runs in d['runs']:
            for key, value in runs.items():
                if key == 'text':
                    description = f"{description} {value}"
        return description

def get_comments(video_url, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    response = session.get(video_url)
    loaded_comments = []
    
    html = response.text

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    try: 
        chanel = get_chanel(data)   
        title, views = get_title_and_views(data)    
        description = get_description(data)    
        subscribers = get_subscribers(data)    
        date = get_date(data)    
        likes, dislikes = get_likes_and_dislikes(data)    
    except KeyError:
        return

    if chanel and title and views and description and likes and dislikes:   
        id = insert_into_youtube_vidoes(
                chanel=chanel,
                subscribes=subscribers,
                link=video_url,
                title=title,
                description=description,
                likes=likes,
                dislikes=dislikes,
                views=views,
                date=date)
    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(video_url)

    session_token = find_value(html, 'XSRF_TOKEN', 3)
    session_token = session_token.encode('ascii').decode('unicode-escape')

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    for renderer in search_dict(data, 'itemSectionRenderer'):
        ncd = next(search_dict(renderer, 'nextContinuationData'), None)
        if ncd:
            break

    if not ncd:
        # Comments disabled?
        return loaded_comments

    continuations = [(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments')]
    n_comments = 1
    while continuations: 
        continuation, itct, action = continuations.pop()
        response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL,
                                params={action: 1,
                                        'pbj': 1,
                                        'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20201202.06.01'})

        if not response:
            break
        if action == 'action_get_comments':
            section = next(search_dict(response, 'itemSectionContinuation'), {})
            for continuation in section.get('continuations', []):
                ncd = continuation['nextContinuationData']
                continuations.append((ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comments'))
            for item in section.get('contents', []):
                continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                      for ncd in search_dict(item, 'nextContinuationData')])

        elif action == 'action_get_comment_replies':
            continuations.extend([(ncd['continuation'], ncd['clickTrackingParams'], 'action_get_comment_replies')
                                  for ncd in search_dict(response, 'nextContinuationData')])
        comments = search_dict(response, 'commentRenderer')
        for comment in comments:
            sub_text = ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
            comment = sub_text[0]
            try:
                print(comment)
            except OSError:
                pass
            loaded_comments.append(comment)
            success = insert_into_youtube_comments(id,comment)
            if success:
                n_comments = n_comments + 1

        time.sleep(sleep)
    
    video = VideosDB(
                host=DBParameters.HOST,
                user=DBParameters.USER,
                password=DBParameters.PASSWORD,
                db_name=DBParameters.DB_NAME,
                )
    video.update_n_comments(id=id, n_comments=n_comments)
    return loaded_comments


def youtube_scraper(max_results, keywords=None, urls=None):
    loaded_comments = []
    print(keywords)
    if urls:
        Parameters.URLS += urls
    for key_word in keywords:
        results = YoutubeSearch(
            key_word,
            max_results=max_results,
            ).to_dict()
        for result in results:
            url = f'https://www.youtube.com{result["url_suffix"]}'
            Parameters.URLS.append(url)
    for url in Parameters.URLS:
        try:
            comments = get_comments(video_url=url)
            loaded_comments += comments
        except (ValueError, TypeError):
            pass
    return loaded_comments

if __name__ == "__main__":
    c = youtube_scraper(
        keywords=SearchParameters.KEY_WORDS,
        max_results=SearchParameters.MAX_RESULTS
    )