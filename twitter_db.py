import mysql.connector
try:
    from .youtube_db import MyDatabase
except:
    from youtube_db import MyDatabase

class TweetsDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)  
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS tweets (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `account` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
                `tweet_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
                `likes` int(100) NOT NULL,
                `retweets` int(100) NOT NULL,
                `replays` int(100) NOT NULL,
                `published_date` date NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_tweet_info(self,tweet,account,likes,replays,retweets,date):
        sql = "SELECT * FROM tweets"
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        self.cursor.execute(sql)
        for row in self.cursor:
            if row[2] == tweet and account == row[1]:
                print("This tweet is already in data base")
                return False , row[0]
        sql = f"""INSERT INTO tweets (tweet_text,account,likes,retweets,replays,published_date) VALUES (%s,%s,%s,%s,%s,%s)"""
        values = (tweet,account,likes,retweets,replays,date)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        id = self.cursor.lastrowid

        return True ,id



class RetweetDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS twitter_retweet (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `tweet_id` int(100) NOT NULL,
                FOREIGN KEY(tweet_id) REFERENCES tweets(id),
                `retweet` text COLLATE utf8mb4_unicode_ci NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_retweet(self,tweet_id,retweet):
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        sql = "INSERT INTO twitter_retweet (tweet_id, retweet) VALUES (%s,%s)"
        values = (tweet_id,retweet)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        
        return True
