import mysql.connector
try:
    from .youtube_db import MyDatabase
except:
    from youtube_db import MyDatabase

class InstaDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)  
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS insta_posts (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `account` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
                `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
                `likes` int(100) NOT NULL,
                `n_comments` int(100) NOT NULL,
                `published_date` date NOT NULL,
                `content_link` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_post_info(self,account, description, likes, n_comments, published_date,content_link):
        sql = "SELECT * FROM insta_posts"
        self.cursor.execute(sql)
        for row in self.cursor:
            if row[-1] == content_link and account == row[1]:
                print("This post is already in data base")
                return row[0]
        sql = f"""INSERT INTO insta_posts (account, description, likes, n_comments, published_date,content_link) VALUES (%s,%s,%s,%s,%s,%s)"""
        values = (account, description, likes, n_comments, published_date,content_link)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        id = self.cursor.lastrowid

        return id
    
    def update_n_comments(self, n_comments,id):
        self.cursor = self.connection.cursor(buffered=True)  
        sql = f"UPDATE insta_posts SET n_comments = {n_comments} WHERE id = {id}"
        self.cursor.execute(sql)
        self.connection.commit()


class CommentDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS insta_comments (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `post_id` int(100) NOT NULL,
                FOREIGN KEY(post_id) REFERENCES insta_posts(id),
                `comment` text COLLATE utf8mb4_unicode_ci NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_comments(self,post_id,comment):
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        sql = "INSERT INTO insta_comments (post_id, comment) VALUES (%s,%s)"
        values = (post_id,comment)
        self.cursor.execute(sql,values)        
        self.connection.commit()        
        return True
