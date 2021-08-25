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
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS fb_posts (
                `id` int(100) NOT NULL AUTO_INCREMENT,
                `page_name` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
                `description` text COLLATE utf8mb4_unicode_ci,
                `url` text COLLATE utf8mb4_unicode_ci NOT NULL,
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

    def insert_post_info(self,page_name,description,reactions,comments,date,shares, url):
        self.cursor.execute('SET NAMES utf8mb4')
        self.cursor.execute("SET CHARACTER SET utf8mb4")
        self.cursor.execute("SET character_set_connection=utf8mb4")
        sql = "SELECT `id`,`url` FROM fb_posts"
        self.cursor.execute(sql)
        for row in self.cursor:
            if row[1] == url:
                print("This post is already in data base")
                return False, row[0]
        sql = f"""INSERT INTO fb_posts (page_name,`description`,`url`,`like`,love,care,haha,wow,sad,angry,comments_num,shares_num,published_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        values = (page_name, description, url, reactions['like'], reactions['love'], reactions['care'], reactions['haha'], reactions['wow'], reactions['sad'], reactions['angry'], comments, shares, date)
        self.cursor.execute(sql,values)        
        self.connection.commit()
        id = self.cursor.lastrowid
        return True ,id
