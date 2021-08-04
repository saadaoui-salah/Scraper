import dateparser
from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL
from flask_cors import CORS
import concurrent.futures
from scrapers.youtube_scrapper import youtube_scraper
from scrapers.instagrame_scraper import insta_scraper
from scrapers.twitter_scraper import twitter_scraper
from utils import create_excel_file, create_directory

app = Flask(__name__)
mysql = MySQL(app)

class Parameters:
    HOST = "localhost"
    USER = "root"
    PASSWORD = 'Saadaouisalah0809'
    DB_NAME = 'youtube'
    SECRET_KEY = '3qf465d4g6wc51g35dgs6qg546qd45x2v1'
    API_KEY = 'api_key'

app.secret_key = Parameters.SECRET_KEY
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MYSQL_HOST'] = Parameters.HOST
app.config['MYSQL_USER'] = Parameters.USER
app.config['MYSQL_PASSWORD'] = Parameters.PASSWORD
app.config['MYSQL_DB'] = Parameters.DB_NAME

def execute_sql( sql):
    cursor = mysql.connection.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    return data, cursor

def get_insta_data():
    data, cursor = execute_sql("SELECT * FROM insta_posts")
    if data is not None:
        posts = []
        for row in data:
            cursor.execute("SELECT * FROM insta_comments WHERE post_id = %s",(row[0],))
            post = {}
            post['id'] = row[0]
            post['account'] = row[1]
            post['description'] = row[2]
            post['likes'] = row[3]
            post['n_comments'] = row[4]
            post['published_date'] = row[5]
            post['content_link'] = row[6]
            post['comments'] = []
            for row  in cursor.fetchall():
                print(row)
                comment = {}
                comment['id'] = row[0]
                comment['comment'] = row[2]
                post['comments'].append(comment)
                posts.append(comment)
        return posts

def get_youtube_data():
    data, cursor = execute_sql("SELECT * FROM youtube_videos")
    if data is not None:
        videos = []
        for row in data:
            cursor.execute(f"SELECT * FROM youtube_comments WHERE video_id = {row[0]}")
            video = {}
            video['id'] = row[0]
            video['channel'] = row[1]
            video['subscribers'] = row[2]
            video['link'] = row[3]
            video['title'] = row[4]
            video['description'] = row[5]
            video['likes'] = row[6]
            video['dislikes'] = row[7]
            video['views'] = row[8]
            video['published_date'] = row[1]
            video['n_comments'] = row[1]
            video['comments'] = []
            for row in cursor.fetchall():
                comment = {}
                comment['id'] = row[0]
                comment['comment'] = row[2]
                video['comments'].append(comment)
            videos.append(video)
    return videos

def get_twiiter_data():
    data, cursor = execute_sql("SELECT * FROM tweets")
    if data is not None:
        tweets = []
        for row in data:
            cursor.execute(f"SELECT * FROM twitter_retweets WHERE tweet_id = {row[0]}")
            tweet = {}
            tweet['id'] = row[0]
            tweet['account'] = row[1]
            tweet['tweet_text'] = row[2]
            tweet['likes'] = row[3]
            tweet['retweets'] = row[4]
            tweet['replays'] = row[5]
            tweet['published_date'] = row[6]
            tweet['comments'] = []
            for row in cursor.fetchall():
                comment = {}
                comment['id'] = row[0]
                comment['comment'] = row[1]
                tweet['comments'].append(comment)
            tweets.append(tweet)
        return tweets

def implement_comments(data):
    comments = []
    for row in data:
        comment = {}
        comment['id'] = row[0]
        comment['comment'] = row[1]
        date  = row[2]
        date = dateparser.parse(str(date))
        m = date.month
        d = date.day
        y = date.year
        comment['date'] = f"{y}-{m}-{d}"
        comments.append(comment)
    return comments

def order_by_date():
    sql = f"""SELECT insta_comments.id, insta_comments.comment, insta_posts.published_date
                FROM youtube.insta_comments
                INNER JOIN youtube.insta_posts
                ON insta_comments.post_id = insta_posts.id
                UNION ALL
                SELECT youtube_comments.id, youtube_comments.comment, youtube_videos.published_date
                FROM youtube.youtube_comments
                INNER JOIN youtube.youtube_videos
                ON youtube_comments.video_id = youtube_videos.id 
                UNION ALL
                SELECT 
                twitter_retweet.id, twitter_retweet.retweet, tweets.published_date
                FROM youtube.twitter_retweet
                INNER JOIN youtube.tweets
                ON twitter_retweet.tweet_id = tweets.id
                order by published_date                  
        """
    data, _ = execute_sql(sql)
    comments = implement_comments(data)
    return comments

def get_insta_comments():
    sql= """SELECT insta_comments.id, insta_comments.comment, insta_posts.published_date
            FROM youtube.insta_comments
            INNER JOIN youtube.insta_posts
            ON insta_comments.post_id = insta_posts.id"""
    data, _ = execute_sql(sql)
    comments = implement_comments(data)
    return comments

def get_twitter_comments():
    sql= """SELECT twitter_retweet.id, twitter_retweet.retweet, tweets.published_date
            FROM youtube.twitter_retweet
            INNER JOIN youtube.tweets
            ON twitter_retweet.tweet_id = tweets.id"""
    data, _ = execute_sql(sql)
    comments = implement_comments(data)
    return comments

def get_youtube_comments():
    sql= """SELECT youtube_comments.id, youtube_comments.comment, youtube_videos.published_date
            FROM youtube.youtube_comments
            INNER JOIN youtube.youtube_videos
            ON youtube_comments.video_id = youtube_videos.id """
    data, _ = execute_sql(sql)
    comments = implement_comments(data)
    return comments

def search(keyword):
    keyword = str(keyword)
    sql = f"""SELECT insta_comments.id, insta_comments.comment, insta_posts.published_date
              FROM youtube.insta_comments
              INNER JOIN youtube.insta_posts
              ON insta_comments.post_id = insta_posts.id
              where insta_comments.comment like '%{keyword}%'
              UNION ALL
              SELECT youtube_comments.id, youtube_comments.comment, youtube_videos.published_date
              FROM youtube.youtube_comments
              INNER JOIN youtube.youtube_videos
              ON youtube_comments.video_id = youtube_videos.id 
              where youtube_comments.comment like '%{keyword}%'
              UNION ALL
              SELECT 
              twitter_retweet.id, twitter_retweet.retweet, tweets.published_date
              FROM youtube.twitter_retweet
              INNER JOIN youtube.tweets
              ON twitter_retweet.tweet_id = tweets.id
              where twitter_retweet.retweet like '%{keyword}%' """
    data, _ = execute_sql(sql)
    comments = implement_comments(data)
    return comments


@app.route('/youtube/<key>')
def youtube_data(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            youtube_videos = get_youtube_data()
            return jsonify(youtube_videos)
    return "You are not authorized"

@app.route('/instagrame/<key>')
def insta_data(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            insta_posts = get_insta_data()
            return jsonify(insta_posts)
    return "You are not authorized"

@app.route('/twiiter/<key>')
def twiiter_data(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            insta_posts = get_twiiter_data()
            return jsonify(insta_posts)
    return "You are not authorized"

@app.route('/insta_comments/<key>')
def insta_comments(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            insta_comments = get_insta_comments()
            return jsonify(insta_comments)
    return "You are not authorized"

@app.route('/twitter_comments/<key>')
def twitter_comments(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            twitter_comments = get_twitter_comments()
            return jsonify(twitter_comments)
    return "You are not authorized"
    
@app.route('/youtube_comments/<key>')
def youtube_comments(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            twitter_comments = get_youtube_comments()
            return jsonify(twitter_comments)
    return "You are not authorized"

@app.route('/order_by_date/<key>')
def ordered(key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            twitter_comments = order_by_date()
            return jsonify(twitter_comments)
    return "You are not authorized"

@app.route('/search/<key_word>/<key>')
def search_(key_word,key):
    if request.method == 'GET':
        if key == Parameters.API_KEY:
            twitter_comments = search(key_word)
            return jsonify(twitter_comments)
    return "You are not authorized"

@app.route("/")
def index():
    return render_template("table.html" )

def split_urls(urls):
    insta = []
    youtube = []
    twitter = []
    for url in urls:
        if 'https://www.youtube.com/watch?v=' in url:
            youtube.append(url)
        elif 'https://www.instagram.com/p/' in url:
            insta.append(url)
        elif 'https://twitter.com/' in url and '/status/' in url:
            twitter.append(url)
        else:
            pass
    return insta, youtube, twitter

def scrape_from_youtube(max_results, urls, keywords):
    if max_results:
        print("from youtube")
        comments = youtube_scraper(max_results,urls,keywords)
        return comments
    return []

def scrape_from_insta(max_results, urls, keywords):
    if max_results:
        print("from insta")
        comments = insta_scraper(max_results, urls, keywords)
        return comments 
    return []

def scrape_from_twitter(max_results, urls, keywords):
    if max_results:
        print("from twitter")
        comments = twitter_scraper(max_results, urls, keywords)
        return comments
    return []

def validate_file_creation(filename, threading, dir):
    if len(threading.result()) > 0 :
        create_excel_file(filename, threading.result(), dir)

@app.route("/scraper", methods=["POST", "GET"])
def launch_scrapers():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        insta_urls, youtube_urls, twitter_urls = split_urls(data['urls'])
        with concurrent.futures.ThreadPoolExecutor() as executor:
            insta = executor.submit(
                scrape_from_insta,
                data['instagrame'],
                data['keywords'],
                insta_urls
                )
            youtube = executor.submit(
                scrape_from_youtube,
                data['youtube'],
                data['keywords'],
                youtube_urls
                )
            twitter = executor.submit(
                scrape_from_twitter,
                data['twitter'],
                data['keywords'],
                twitter_urls
                )
            dir_name = create_directory()
            validate_file_creation("instagrame", insta, dir_name) 
            validate_file_creation("youtube", youtube, dir_name) 
            validate_file_creation("twitter", twitter, dir_name)
            comments = insta.result() + youtube.result() + twitter.result()
        return jsonify(comments)

    return render_template('form.html')



if __name__ == "__main__":
    app.run(debug=True)