from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QRadioButton, QDialog, QLineEdit, QHBoxLayout, QMessageBox, QCheckBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from backend import DatabaseManager, MovieScraperThread
import random
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from backend import r_url

class MovieScraperThread(QThread): #тестовый пуш гитхаба
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
    def __init__(self, db_manager, run_app_func):
        super().__init__()
        self.db_manager = db_manager
        self.run_app_func = run_app_func
        self.movie_scraper_thread = MovieScraperThread(self.db_manager)
        self.initUI()


    def initUI(self):
        self.setWindowTitle('Rflix')
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.status_label = QLabel('Нажмите кнопку, чтобы перенести фильмы в базу данных')
        self.layout.addWidget(self.status_label)

        self.scrape_button = QPushButton('Перенос фильмов')
        self.scrape_button.clicked.connect(self.scrape_movies)
        self.layout.addWidget(self.scrape_button)

        self.pick_random_button = QPushButton('Выбрать случайный фильм')
        self.pick_random_button.clicked.connect(self.pick_random_movie)
        self.layout.addWidget(self.pick_random_button)

        self.settings_button = QPushButton('Настройки')
        self.settings_button.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_button)

        self.poster_label = QLabel(self)
        self.layout.addWidget(self.poster_label)

        self.central_widget.setLayout(self.layout)
        self.movies = []

        button_style = """
                   QPushButton {
                       background-color: #4CAF50; /* Green background */
                       color: white; /* White text */
                       font-size: 14px;
                       border: none;
                       padding: 10px 15px;
                       margin-top: 10px;
                       border-radius: 5px; /* Rounded corners */
                   }

                   QPushButton:hover {
                       background-color: #3e8e41; /* Darker green on hover */
                   }
               """

        self.scrape_button.setStyleSheet(button_style)
        self.pick_random_button.setStyleSheet(button_style)
        self.settings_button.setStyleSheet(button_style)

    def reload_ui(self, reload):
        if reload:
            self.initUI()

    def show_settings(self):
        settings_widget = SettingsWidget(self)
        settings_widget.go_home_signal.connect(self.reload_ui)
        self.setCentralWidget(settings_widget)

    def close_app(self):
        self.close()

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
        """)

    def scrape_movies(self):
        if not self.movie_scraper_thread.isRunning():
            self.movie_scraper_thread.start()
            self.status_label.setText('Идет процесс переноса фильмов в базу данных. Пожалуйста, подождите...')

    def scrape_movies_finished(self, new_movies):
        self.movies = new_movies

        if new_movies:
            self.status_label.setText('Фильмы успешно перенесены и сохранены в базе данных')
        else:
            self.status_label.setText('Все фильмы уже есть в базе данных. Ничего не добавлено.')

    def display_error(self, error_message):
        self.status_label.setText(error_message)
        self.movie_scraper_thread.quit()

    def display_movie_poster(self, poster_url):
        response = requests.get(poster_url)
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        scaled_pixmap = pixmap.scaled(200, 300, aspectRatioMode=Qt.KeepAspectRatio)
        self.poster_label.setPixmap(scaled_pixmap)

    def pick_random_movie(self):
        if not self.movies:
            self.movies = self.db_manager.get_all_movies()

        if not self.movies:
            self.status_label.setText('Нет доступных фильмов. Сперва перенесите их.')
            return

        random_movie = random.choice(self.movies)
        title, poster_url = random_movie
        self.display_movie_poster(poster_url)
        self.status_label.setText(f'Случайно выбранный фильм: {title}')

class SettingsWidget(QWidget):
    go_home_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.home_button = QPushButton('Домой', self)
        self.home_button.clicked.connect(self.go_home)

        layout.addWidget(self.home_button)

    def go_home(self):
        self.hide()
        self.go_home_signal.emit(True)

class LoginDialog(QDialog):
    def set_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
                padding: 20px;
            }

            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }

            QLineEdit {
                font-size: 14px;
                padding: 5px;
                border: 2px solid #ccc;
                border-radius: 5px;
            }

            QPushButton {
                font-size: 14px;
                padding: 5px 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #4CAF50;
                color: white;
            }

            QPushButton:hover {
                background-color: #3e8e41;
            }
        """)

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.settings = QSettings("MyCompany", "MyApp")
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Вход/Регистрация')

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.username_label = QLabel('Имя пользователя:')
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)

        self.password_label = QLabel('Пароль:')
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)

        self.remember_checkbox = QCheckBox('Запомнить меня')
        layout.addWidget(self.remember_checkbox)

        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton('Регистрация')
        self.register_button.clicked.connect(self.register)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        layout.addLayout(button_layout)

        if self.settings.contains("username"):
            self.username_edit.setText(self.settings.value("username"))
            self.password_edit.setText(self.settings.value("password"))
            self.remember_checkbox.setChecked(True)

        self.set_style()

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not self.db_manager.validate_credentials(username, password):
            QMessageBox.warning(self, 'Ошибка', 'Неверные имя пользователя или пароль.')
            return

        if self.remember_checkbox.isChecked():
            self.settings.setValue("username", username)
            self.settings.setValue("password", password)

        self.accept()

    def register(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not self.db_manager.register_user(username, password):
            QMessageBox.warning(self, 'Ошибка', 'Не удалось зарегистрироваться.')
            return

        QMessageBox.information(self, 'Успех', 'Пользователь успешно зарегистрирован.')
        self.accept()


