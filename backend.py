import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QRadioButton, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
import time
import requests
from PyQt5.QtGui import QPixmap
import sqlite3


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
    def __init__(self, db_file="movies.db"):
        self.conn = sqlite3.connect(db_file)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                poster_url TEXT
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        self.conn.commit()

    def login_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ? AND password = ?', (username, password))
        count = cursor.fetchone()[0]
        return count > 0

    def movie_exists(self, title):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM movies WHERE title = ?', (title,))
        count = cursor.fetchone()[0]
        return count > 0

    def insert_movie(self, title, poster_url):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO movies (title, poster_url) VALUES (?, ?)', (title, poster_url))
        self.conn.commit()

    def get_all_movies(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT title, poster_url FROM movies')
        return cursor.fetchall()


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
            "img", {"class": "styles_image__gRXvn styles_mediumSizeType__fPzdD image styles_root__DZigd",
                    "data-tid": "d813cf42"}
        )

        new_movies = []
        for movie_element, poster_element in zip(movie_elements, poster_elements):
            title = movie_element.text.strip()
            poster_url = f"https:{poster_element['src']}"

            if not self.db_manager.movie_exists(title):
                new_movies.append((title, poster_url))
                self.db_manager.insert_movie(title, poster_url)
                time.sleep(1)

        self.finished.emit(new_movies)
        driver.quit()


class MovieScraperApp(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.login_register_window = LoginRegisterApp(self.db_manager, self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Рандомайзер фильмов')
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.status_label = QLabel('Нажмите кнопку, чтобы перенести фильмы в базу данных')
        self.layout.addWidget(self.status_label)
        self.scrape_button = QPushButton('Перенос фильмов')
        self.scrape_button.clicked.connect(self.show_movie_scraper)
        self.layout.addWidget(self.scrape_button)
        self.pick_random_button = QPushButton('Выбрать случайный фильм')
        self.pick_random_button.clicked.connect(self.pick_random_movie)
        self.layout.addWidget(self.pick_random_button)
        self.poster_label = QLabel(self)
        self.layout.addWidget(self.poster_label)
        self.central_widget.setLayout(self.layout)
        self.movies = []
        self.light_theme_radio = QRadioButton('Светлая тема', self)
        self.dark_theme_radio = QRadioButton('Темная тема', self)
        self.light_theme_radio.setChecked(True)  # Устанавливаем светлую тему по умолчанию
        self.light_theme_radio.toggled.connect(self.toggle_theme)
        self.dark_theme_radio.toggled.connect(self.toggle_theme)

        self.layout.addWidget(self.light_theme_radio)
        self.layout.addWidget(self.dark_theme_radio)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }

            QLabel {
                font-size: 16px;
                color: #333;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                border: none;
                padding: 10px 15px;
                margin-top: 10px;
            }

            QLineEdit {
                font-size: 14px;
                padding: 5px;
                margin-top: 5px;
            }
        """)

    def toggle_theme(self):
        if self.light_theme_radio.isChecked():
            self.set_light_theme()
        elif self.dark_theme_radio.isChecked():
            self.set_dark_theme()

    def set_light_theme(self):
        self.setStyleSheet("""
              QMainWindow {
                  background-color: #f0f0f0;
              }

              QLabel {
                  font-size: 16px;
                  color: #333;
              }

              QPushButton {
                  background-color: #4CAF50;
                  color: white;
                  font-size: 14px;
                  border: none;
                  padding: 10px 15px;
                  margin-top: 10px;
              }

              QLineEdit {
                  font-size: 14px;
                  padding: 5px;
                  margin-top: 5px;
              }
              """)

    def set_dark_theme(self):
        self.setStyleSheet("""
              QMainWindow {
                  background-color: #333;
              }

              QLabel {
                  font-size: 16px;
                  color: #fff;
              }

              QPushButton {
                  background-color: #4CAF50;
                  color: white;
                  font-size: 14px;
                  border: none;
                  padding: 10px 15px;
                  margin-top: 10px;
              }

              QLineEdit {
                  font-size: 14px;
                  padding: 5px;
                  margin-top: 5px;
              }
              """)

    def show_movie_scraper(self):
        self.movie_scraper_thread = MovieScraperThread(self.db_manager)
        self.movie_scraper_thread.finished.connect(self.scrape_movies_finished)
        self.movie_scraper_thread.start()
        self.status_label.setText('Идет процесс переноса фильмов в базу данных. Пожалуйста, подождите...')

    def scrape_movies_finished(self, new_movies):
        self.movies.extend(new_movies)

        if new_movies:
            self.status_label.setText('Фильмы успешно перенесены и сохранены в базе данных')
        else:
            self.status_label.setText('Все фильмы уже есть в базе данных. Ничего не добавлено.')

    def display_movie_poster(self, poster_url):
        response = requests.get(poster_url)
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        scaled_pixmap = pixmap.scaled(200, 300, aspectRatioMode=Qt.KeepAspectRatio)
        self.poster_label.setPixmap(scaled_pixmap)

    def pick_random_movie(self):
        if not self.movies:
            self.status_label.setText('Нет доступных фильмов. Сперва перенесите их.')
            return

        random_movie = random.choice(self.movies)
        title, poster_url = random_movie
        self.display_movie_poster(poster_url)
        self.status_label.setText(f'Случайно выбранный фильм: {title}')


class LoginRegisterApp(QWidget):
    def __init__(self, db_manager, main_app):
        super().__init__()
        self.db_manager = db_manager
        self.main_app = main_app
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Вход/Регистрация')
        self.layout = QVBoxLayout()
        self.username_label = QLabel('Имя пользователя:')
        self.username_input = QLineEdit(self)
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.password_label = QLabel('Пароль:')
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.login_button = QPushButton('Вход', self)
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)
        self.register_button = QPushButton('Регистрация', self)
        self.register_button.clicked.connect(self.register)
        self.layout.addWidget(self.register_button)
        self.setLayout(self.layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }

            QLabel {
                font-size: 16px;
                color: #333;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                border: none;
                padding: 10px 15px;
                margin-top: 10px;
            }

            QLineEdit {
                font-size: 14px;
                padding: 5px;
                margin-top: 5px;
            }
        """)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.db_manager.login_user(username, password):
            self.close()
            self.main_app.show()
        else:
            QMessageBox.warning(self, 'Ошибка входа', 'Неверное имя пользователя или пароль', QMessageBox.Ok)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username and password:
            self.db_manager.register_user(username, password)
            QMessageBox.information(self, 'Успешная регистрация', 'Пользователь зарегистрирован', QMessageBox.Ok)
        else:
            QMessageBox.warning(self, 'Ошибка регистрации', 'Введите имя пользователя и пароль', QMessageBox.Ok)


def run_app():
    app = QApplication(sys.argv)
    login_register_window = LoginRegisterApp(DatabaseManager(), MovieScraperApp(DatabaseManager()))
    login_register_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    run_app()