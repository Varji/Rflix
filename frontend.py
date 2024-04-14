from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QDialog, QLineEdit, QHBoxLayout, QMessageBox, QCheckBox, QRadioButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from backend import DatabaseManager, MovieScraperThread
import random
import requests
from PyQt5.QtCore import pyqtSignal, QSettings, QPropertyAnimation, QRect
import webbrowser

class MovieScraperApp(QMainWindow):
    def __init__(self, db_manager, run_app_func):
        super().__init__()
        self.db_manager = db_manager
        self.run_app_func = run_app_func
        self.movie_scraper_thread = MovieScraperThread(self.db_manager)
        self.initUI()
        self.set_light_theme()


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

        self.watch_online_button = QPushButton('Смотреть онлайн')
        self.watch_online_button.clicked.connect(self.watch_online)
        self.layout.addWidget(self.watch_online_button)
        self.watch_online_button.hide()
        self.settings_button = QPushButton('Настройки')
        self.settings_button.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_button)

        self.poster_label = QLabel(self)
        self.layout.addWidget(self.poster_label)

        self.central_widget.setLayout(self.layout)
        self.movies = []

        button_style = """
                   QPushButton {
                       background-color: #4CAF50; 
                       color: white; 
                       font-size: 14px;
                       border: none;
                       padding: 10px 15px;
                       margin-top: 10px;
                       border-radius: 5px;
                   }

                   QPushButton:hover {
                       background-color: #3e8e41;
                   }
               """

        self.scrape_button.setStyleSheet(button_style)
        self.pick_random_button.setStyleSheet(button_style)
        self.settings_button.setStyleSheet(button_style)
        self.watch_online_button.setStyleSheet(button_style)

    def reload_ui(self, reload):
        if reload:
            self.initUI()

    def show_settings(self):
        settings_widget = SettingsWidget(self)
        settings_widget.go_home_signal.connect(self.reload_ui)
        self.setCentralWidget(settings_widget)

    def close_app(self):
        self.close()

    def set_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: 
                f0f0f0;
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

    def toggle_theme(self):
        settings_widget = self.centralWidget()
        if settings_widget and isinstance(settings_widget, SettingsWidget):
            if settings_widget.light_theme_radio.isChecked():
                self.set_light_theme()
            elif settings_widget.dark_theme_radio.isChecked():
                self.set_dark_theme()

    def show_settings(self):
        settings_widget = SettingsWidget(self)
        settings_widget.go_home_signal.connect(self.reload_ui)
        settings_widget.change_theme_signal.connect(self.toggle_theme)
        self.setCentralWidget(settings_widget)
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
        self.selected_title, self.selected_poster_url, self.selected_film_url = random_movie
        title, poster_url, film_url = random_movie
        self.display_movie_poster(poster_url)
        self.status_label.setText(f'Случайно выбранный фильм: {title}')
        self.watch_online_button.show()

        self.selected_film_url = film_url

    def watch_online(self):
        if not self.selected_film_url:
            self.status_label.setText('Нет доступных фильмов.')
            return

        if self.selected_film_url:

            vip_film_url = self.selected_film_url.replace('kinopoisk.ru', 'kinopoisk.vip')
            webbrowser.open(vip_film_url)
            self.status_label.setText(f'Открытие фильма в браузере: {vip_film_url}')
        else:
            self.status_label.setText('Ссылка на фильм отсутствует.')

class SettingsWidget(QWidget):
    go_home_signal = pyqtSignal(bool)
    change_theme_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(0, parent.height(), parent.width(), parent.height())
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.home_button = QPushButton('Домой', self)
        self.home_button.clicked.connect(self.go_home)

        layout.addWidget(self.home_button)

        self.light_theme_radio = QRadioButton('Светлая тема', self)
        self.dark_theme_radio = QRadioButton('Темная тема', self)

        layout.addWidget(self.light_theme_radio)
        layout.addWidget(self.dark_theme_radio)

        self.light_theme_radio.toggled.connect(self.toggle_theme)
        self.dark_theme_radio.toggled.connect(self.toggle_theme)

    def go_home(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(0, self.parent().height(), self.parent().width(), self.parent().height()))
        self.animation.finished.connect(lambda: self.hide())
        self.animation.start()

        self.go_home_signal.emit(True)

    def showEvent(self, event):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(self.parent().width(), 0, self.parent().width(), self.parent().height()))
        self.animation.setEndValue(QRect(0, 0, self.parent().width(), self.parent().height()))
        self.animation.start()

    def toggle_theme(self):
        self.change_theme_signal.emit()

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

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Пожалуйста, введите имя пользователя и пароль.')
            return

        if self.db_manager.user_exists(username):
            QMessageBox.warning(self, 'Ошибка', 'Такой пользователь уже существует.')
            return

        if not self.db_manager.register_user(username, password):
            QMessageBox.warning(self, 'Ошибка', 'Не удалось зарегистрироваться.')
            return

        QMessageBox.information(self, 'Успех', 'Пользователь успешно зарегистрирован.')
        self.accept()
