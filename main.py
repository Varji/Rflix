import sys
from PyQt5.QtWidgets import QApplication
from frontend import LoginDialog, MovieScraperApp
from backend import DatabaseManager

def run_app():
    app = QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec_() == LoginDialog.Accepted:
        db_manager = DatabaseManager()
        mainWin = MovieScraperApp(db_manager, run_app)
        mainWin.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()