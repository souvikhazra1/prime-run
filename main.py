import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import ui_main_window
from gi.repository import Gio
import math
import time
import subprocess

APP_ITEM_MIN_WIDTH = 150
ALL_CATEGORY = 'All'
all_apps = list()
all_categories = [ALL_CATEGORY, 'Development', 'Education', 'Game', 'Graphics', 'Network', 'Office', 'Settings', 'System', 'Utility']
selected_category = ALL_CATEGORY

application = None
rendering = True

class MainApp(QtWidgets.QMainWindow, ui_main_window.Ui_MainWindow):
    last_col_count = 0
    last_screen_width = 0
    last_btn_checked = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.searchET.textChanged.connect(self.filter)

    def filter(self):
        self.prepare_app_list(True)

    def prepare_cat_list(self):
        for cat in all_categories:
            cat_btn = QtWidgets.QPushButton()
            cat_btn.setText(cat)
            cat_btn.setCheckable(True)
            if cat == ALL_CATEGORY:
                cat_btn.setChecked(True)
                self.last_btn_checked = cat_btn
            self.categoryList.addWidget(cat_btn)
            cat_btn.clicked.connect(lambda state, i=cat_btn: self.select_category(i))

    def select_category(self, btn):
        global selected_category
        
        selected_category = btn.text()
        if self.last_btn_checked:
            self.last_btn_checked.setChecked(False)
        btn.setChecked(True)
        self.last_btn_checked = btn
        self.prepare_app_list(True)

    def prepare_app_list(self, force=False):
        geometry = self.geometry()
        screen_width = geometry.width()
        if not force and self.last_screen_width == screen_width:
            return
        self.last_screen_width = screen_width
        col_count = math.floor(geometry.width() / APP_ITEM_MIN_WIDTH)
        if not force and self.last_col_count == col_count:
            return
        self.last_col_count = col_count

        filter_keyword = self.searchET.toPlainText().lower()

        for _i in range(self.appGrid.count()):
            self.appGrid.itemAt(0).widget().close()
            self.appGrid.takeAt(0)

        idx = 0
        for app in all_apps:
            if selected_category != ALL_CATEGORY:
                if selected_category not in app['categories']:
                    continue
            if len(filter_keyword) > 0 and app['name'].lower().find(filter_keyword) == -1:
                continue

            app_item = QtWidgets.QWidget()
            app_item_layout = QtWidgets.QVBoxLayout(app_item)
            app_icon_label = QtWidgets.QLabel()
            app_icon_label.setPixmap(QtGui.QIcon.fromTheme(app['icon']).pixmap(64, 64))
            app_item_layout.addWidget(app_icon_label, 0, QtCore.Qt.AlignHCenter)

            app_text_label = QtWidgets.QLabel()
            app_text_label.minimumWidth = APP_ITEM_MIN_WIDTH
            app_text_label.setText(app['name'])
            app_text_label.setWordWrap(True)
            app_text_label.setAlignment(QtCore.Qt.AlignHCenter)
            app_item_layout.addWidget(app_text_label, 0, QtCore.Qt.AlignHCenter)
            app_item.setMaximumSize(QtCore.QSize(16777215, 120))
            app_item.setProperty('className', 'app-item')
            app_item.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            app_item.mouseReleaseEvent = (lambda state, i=app['command']: self.start_app(i))

            self.appGrid.addWidget(app_item, math.floor(idx / col_count) + 1, (idx % col_count) + 1, 1, 1)
            idx = idx + 1

    def start_app(self, command):
        print('prime-run ' + command)
        subprocess.Popen(['prime-run', *command.split(' ')], stdout=sys.stdout, stderr=sys.stdout, stdin=sys.stdout)

    def resizeEvent(self, event):
        if not rendering:
            render_started()
            QtCore.QTimer.singleShot(200, self.prepare_app_list)
            QtCore.QTimer.singleShot(700, render_finished)

def get_app_name(el):
    return el['name']

def render_started():
    global rendering
    rendering = True

def render_finished():
    global rendering
    rendering = False

def get_app_list():
    apps = Gio.AppInfo.get_all()
    app_names = list()
    for app in apps:
        icon = app.get_icon()
        if icon:
            name = app.get_display_name()
            if name not in app_names:
                app_names.append(name)
                item = {'name': name, 'icon': icon.to_string(), 'categories': [], 'command': app.get_commandline()}
                categories = app.get_categories()
                if categories:
                    category_list = categories.split(';')
                    item['categories'] = category_list
                all_apps.append(item)

    all_apps.sort(key=get_app_name)

        
def main():
    global application, rendering

    application = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()

    get_app_list()
    window.prepare_cat_list()
    QtCore.QTimer.singleShot(500, window.prepare_app_list)
    QtCore.QTimer.singleShot(1000, render_finished)

    application.exec_()

if __name__ == '__main__':
    main()
