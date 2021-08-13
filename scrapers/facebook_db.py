import mysql.connector
try:
    from .youtube_db import MyDatabase
except:
    from youtube_db import MyDatabase

class FacbookPostDB():
    def __init__(self,host,user,password,db_name):
        db = MyDatabase(host,user,password,db_name)
        self.connection = db.connect()
        self.db_name = db_name

    def create_table(self):
        self.cursor = self.connection.cursor(buffered=True)  
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS tweets (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `page_name` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
                `description` text COLLATE utf8mb4_unicode_ci,
                `like` int(100) NOT NULL,
                `love` int(100) NOT NULL,
                `care` int(100) NOT NULL,
                `haha` int(100) NOT NULL,
                `wow` int(100) NOT NULL,
                `sad` int(100) NOT NULL,
                `angry` int(100) NOT NULL,
                `comments_num` int(100) NOT NULL,
                `shares_num` int(100) NOT NULL,
                `published_date` date NOT NULL,
                PRIMARY KEY (`id`)
                )
            """)

    def insert_post_info(self,page_name,description,reactions,comments,date,shares):
        sql = "SELECT * FROM tweets"
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        self.cursor.execute(sql)
        sql = f"""INSERT INTO tweets (page_name, description, like, love, care, haha, wow, sad, angry, comments_num, shares_num, published_date) VALUES (%s,%s,%s,%s,%s,%s)"""
        values = (page_name, description, reactions['like'], reactions['love'], reactions['care'], reactions['haha'], reactions['wow'], reactions['sad'], reactions['angry'], comments, shares, date)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        id = self.cursor.lastrowid

        return True ,id
