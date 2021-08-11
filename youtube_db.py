import mysql.connector



class MyDatabase():
    def __init__(self,host,user,password,db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        mydb = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            charset="utf8mb4"
        )
        cursor = mydb.cursor()
        db = cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.db_name}')

    def connect(self):
        connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        return connection

class VideosDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor()  
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS youtube_videos (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `youtube_channel` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
                `channel_subscribers` int(11) NOT NULL,
                `video_link` varchar(500) UNIQUE COLLATE utf8mb4_unicode_ci NOT NULL,
                `video_title` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
                `video_description` text COLLATE utf8mb4_unicode_ci,
                `likes` int(11) NOT NULL,
                `dislikes` int(11) NOT NULL,
                `n_views` int(11) NOT NULL,
                `published_date` date NOT NULL,
                `n_comments` int(11) NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_video_info(self,chanel,subscribes,link,title,description,likes,dislikes,views,date):
        try:
            sql = f"""INSERT INTO youtube_videos (youtube_channel,channel_subscribers,video_link,video_title,video_description,likes,dislikes,n_views,published_date,n_comments) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            n_comments = 0
            values = (chanel,subscribes,link,title,description,likes,dislikes,views,date,n_comments)
            self.cursor.execute(sql,values)        
            self.connection.commit()
            id = self.cursor.lastrowid
            return id
        except mysql.connector.errors.IntegrityError:
            sql = "SELECT * FROM youtube_videos"
            self.cursor.execute(sql)
            for row in self.cursor:
                if row[3] == link : 
                    id = row [0]
                    return id
         

    def update_n_comments(self, n_comments,id):
        self.cursor = self.connection.cursor(buffered=True)  
        sql = f"UPDATE youtube_videos SET n_comments = {n_comments} WHERE id = {id}"
        self.cursor.execute(sql)
        self.connection.commit()

class CommentDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS youtube_comments (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `video_id` int(11) NOT NULL,
                FOREIGN KEY(video_id) REFERENCES youtube_videos(id),
                `comment` text COLLATE utf8mb4_unicode_ci NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_comments(self,video_id,comment):
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        sql = "INSERT INTO youtube_comments (video_id, comment) VALUES (%s,%s)"
        values = (video_id,comment)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        
        return True
