import sqlite3
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PyQt5.QtCore import QThread, pyqtSignal

r_url = (
    "https://www.kinopoisk.ru/lists/movies/top500/?utm_referrer=www.google.com",
    "https://www.kinopoisk.ru/lists/movies/top500/?page=2",
    "https://www.kinopoisk.ru/lists/movies/top500/?page=3",
    "https://www.kinopoisk.ru/lists/movies/top500/?page=4",
    "https://www.kinopoisk.ru/lists/movies/popular-films/",
    "https://www.kinopoisk.ru/lists/movies/popular-films/?page=2",
    "https://www.kinopoisk.ru/lists/movies/popular-films/?page=3"
)

class DatabaseManager:
    def __init__(self, db_file="database.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.create_movie_table()
        self.create_user_table()

    def create_movie_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS movies (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT,
                   poster_url TEXT,
                   film_url TEXT
               )
           ''')
        self.conn.commit()

    def create_user_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE,
                   password TEXT
               )
           ''')
        self.conn.commit()

    def insert_movie(self, title, poster_url, film_url):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO movies (title, poster_url, film_url) VALUES (?, ?, ?)',
                       (title, poster_url, film_url))
        self.conn.commit()

    def get_all_movies(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT title, poster_url, film_url FROM movies')
        return cursor.fetchall()

    def movie_exists(self, title):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM movies WHERE title = ?', (title,))
        count = cursor.fetchone()[0]
        return count > 0

    def clear_null_rows(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM movies WHERE title IS NULL OR poster_url IS NULL")
        self.conn.commit()

    def register_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

    def validate_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? AND password = ?", (username, password))
        count = cursor.fetchone()[0]

        if count == 0:
            return False
        return True

    def user_exists(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
        count = cursor.fetchone()[0]
        return count > 0

class MovieScraperThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def run(self):
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        url = random.choice(r_url)
        driver.get(url)
        driver.implicitly_wait(10)

        while True:
            if "captcha" in driver.current_url:
                time.sleep(5)
            else:
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")

        movie_elements = soup.find_all(
            "span", {"class": "styles_mainTitle__IFQyZ styles_activeMovieTittle__kJdJj", "data-tid": "4502216a"}
        )

        poster_elements = soup.find_all(
            "img", {"class": "styles_image__gRXvn styles_mediumSizeType__fPzdD image styles_root__DZigd","data-tid": "d813cf42"}
        )
        film_url_elements = soup.find_all(
            "a", {"class": "base-movie-main-info_link__YwtP1", "data-tid":"d4e8d214"}
        )

        new_movies = []
        for movie_element, poster_element, film_url_element in zip(movie_elements, poster_elements, film_url_elements):
            title = movie_element.text.strip()
            poster_url = f"https:{poster_element['src']}"
            film_url = film_url_element['href']

            if not self.db_manager.movie_exists(title) and film_url.startswith("/film/"):
                film_url = f"https://www.kinopoisk.ru{film_url}"
                new_movies.append((title, poster_url, film_url))
                self.db_manager.insert_movie(title, poster_url, film_url)
                time.sleep(1)

        self.finished.emit(new_movies)
        driver.quit()

