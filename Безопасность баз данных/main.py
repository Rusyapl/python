import datetime
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QApplication, QMessageBox, QLineEdit, QPushButton, QComboBox, \
    QLabel, QInputDialog, QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView, \
    QSpinBox, QTableView, QMenuBar, QAction, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import subprocess
import os
import psycopg2

def connect_db(login, password):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=login,
            password=password,
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_table_names(conn):
    table_names = []
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    for row in cursor.fetchall():
        table_names.append(row[0])
    return table_names

class InputDialog(QDialog):
    def __init__(self, column_names, parent=None):
        super(InputDialog, self).__init__(parent)
        self.setWindowTitle("Введите данные")
        self.layout = QFormLayout(self)
        self.inputs = []
        for name in column_names:
            label = QLabel(name)
            line_edit = QLineEdit()
            self.layout.addRow(label, line_edit)
            self.inputs.append(line_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.layout.addRow(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

class BackupSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(BackupSettingsDialog, self).__init__(parent)
        self.setWindowTitle("Настройки автоматического бэкапа")
        self.layout = QVBoxLayout(self)

        self.interval_label = QLabel("Интервал резервного копирования (секунды):", self)
        self.layout.addWidget(self.interval_label)

        self.interval_spinbox = QSpinBox(self)
        self.interval_spinbox.setMinimum(30)  # Минимальный интервал 30 секунд
        self.interval_spinbox.setMaximum(3600)  # Максимальный интервал 1 час
        self.interval_spinbox.setValue(300)  # Значение по умолчанию - 5 минут
        self.layout.addWidget(self.interval_spinbox)

        self.start_button = QPushButton("Начать автоматическое резервное копирование", self)
        self.layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.accept)

        self.stop_button = QPushButton("Остановить автоматическое резервное копирование", self)
        self.layout.addWidget(self.stop_button)
        self.stop_button.clicked.connect(self.reject)

class QueryDialog(QDialog):
    def __init__(self, parent=None):
        super(QueryDialog, self).__init__(parent)
        self.setWindowTitle("Выберите запрос")
        self.layout = QVBoxLayout(self)

        self.query_combo = QComboBox(self)
        self.query_combo.addItems([
            "Перечислить лекарства, купленные за последние два дня.",
            "Удалить тех заказчиков, заказы которых были выполнены.",
            "Создать запрос, который выводит среднюю стоимость всех лекарств.",
            "Создать запрос, который содержит фамилию заказчиков, заказавших самое дорогое лекарство, и если он пенсионер сделать для них скидку 2%.",
            "Выполнить запрос, в котором по показанию к применению выводится список лекарств.",
            "Выдать клиентов сделавших более 10 заказов и сделать им скидку 5 %",
            "Получить список лекарств, срок годности которых истекает в течении полутора лет, с указанием производителя и цены.",
            "Показать все заказы клиентов с датами их доставок и статусами доставок, для заказов, которые были сделаны за последние 30 дней.",
        ])
        self.layout.addWidget(self.query_combo)

        self.execute_button = QPushButton("Выполнить запрос", self)
        self.layout.addWidget(self.execute_button)
        self.execute_button.clicked.connect(self.execute_query)

        self.result_view = QTableView(self)
        self.layout.addWidget(self.result_view)

        self.model = QStandardItemModel(self)
        self.result_view.setModel(self.model)

    def execute_query(self):
        query = ""
        if self.query_combo.currentText() == "Перечислить лекарства, купленные за последние два дня.":
            query = """
                select naimenovanie from lekarstvo
                join apteka_i_lekarstvo on lekarstvo.id_lekarstvo = apteka_i_lekarstvo.id_lekarstvo
                join zakaz on apteka_i_lekarstvo.id_apteka_i_lekarstvo = zakaz.id_apteka_i_lekarstvo
                where data_zakaza >= now() - interval '3' day;
                        """
        elif self.query_combo.currentText() == "Удалить тех заказчиков, заказы которых были выполнены.":
            query = """
                DELETE FROM dostavka
                WHERE status_dostavki = 'Доставлено';
                        """
        elif self.query_combo.currentText() == "Создать запрос, который выводит среднюю стоимость всех лекарств.":
            query = """
                select sum(cena)/count(cena) as srednyy from lekarstvo;
                        """
        elif self.query_combo.currentText() == "Создать запрос, который содержит фамилию заказчиков, заказавших самое дорогое лекарство, и если он пенсионер сделать для них скидку 2%.":
            query = """
                select client.familiya,
                case
                    when client.id_client in (1, 3, 7) then lekarstvo.cena * 0.98
                    else lekarstvo.cena
                end as price_with_discount
                from client
                join zakaz on client.id_client = zakaz.id_client
                join apteka_i_lekarstvo on zakaz.id_apteka_i_lekarstvo = apteka_i_lekarstvo.id_apteka_i_lekarstvo
                join lekarstvo on apteka_i_lekarstvo.id_lekarstvo = lekarstvo.id_lekarstvo
                where lekarstvo.cena = (select max(cena) from lekarstvo)
                        """
        elif self.query_combo.currentText() == "Выполнить запрос, в котором по показанию к применению выводится список лекарств.":
            query = """
                SELECT l.naimenovanie AS lekarstvo, p.naimenovanie AS pokazanie
                FROM lekarstvo l
                JOIN lekarstvo_i_ih_primenenie lp ON l.id_lekarstvo = lp.id_lekarstvo
                JOIN pokazanie_k_primeneniu p ON lp.id_pokazanie_k_primeneniu = p.id_pokazanie_k_primeneniu
                WHERE p.naimenovanie = 'Лихорадка';
                        """
        elif self.query_combo.currentText() == "Выдать клиентов сделавших более 10 заказов и сделать им скидку 5 %":
            query = """
                INSERT INTO skidka (id_skidka, id_client, opisanie, procent_skidk)
                SELECT (SELECT COALESCE(MAX(id_skidka), 0) + 1 FROM skidka), id_client, 'Скидка за более 10 заказов', 5
                FROM (
                    SELECT id_client
                    FROM zakaz
                    GROUP BY id_client
                    HAVING COUNT(id_zakaz) > 10
                ) AS eligible_clients;
                select * from skidka
                        """
        elif self.query_combo.currentText() == "Получить список лекарств, срок годности которых истекает в течении полутора лет, с указанием производителя и цены.":
            query = """
                select naimenovanie, proizvoditel, cena, goden_do
                from lekarstvo
                where goden_do between current_date and (current_date + interval '1.5 year');
                            """
        elif self.query_combo.currentText() == "Показать все заказы клиентов с датами их доставок и статусами доставок, для заказов, которые были сделаны за последние 30 дней.":
            query = """
               select zakaz.id_client, zakaz.data_zakaza, dostavka.data_dostavki
                from zakaz
                join dostavka on zakaz.id_zakaz = dostavka.id_zakaz
                where zakaz.data_zakaza >= (current_date - INTERVAL '30 days')
                        """

        conn = connect_db(self.parent().login, self.parent().password)
        if conn:
            cursor = conn.cursor()
            cursor.execute(query)
            self.show_query_result(cursor)
            conn.close()

    def show_query_result(self, cursor):
        self.model.clear()
        self.model.setHorizontalHeaderLabels([i[0] for i in cursor.description])
        for row_number, row_data in enumerate(cursor.fetchall()):
            self.model.insertRow(row_number)
            for col_number, data in enumerate(row_data):
                self.model.setItem(row_number, col_number, QStandardItem(str(data)))

class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.login = None
        self.password = None
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.parent = parent
        self.ulogin = QLineEdit('')
        self.upassword = QLineEdit('')
        self.upassword.setEchoMode(QLineEdit.Password)
        self.pushLog = QPushButton('Авторизация')
        self.pushLog.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                font-size: 12px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        self.pushLog.clicked.connect(self.loga)
        formlayout = QtWidgets.QFormLayout(self.centralwidget)
        formlayout.addRow('Введите логин', self.ulogin)
        formlayout.addRow('Введите пароль', self.upassword)
        formlayout.addRow('', self.pushLog)

    def loga(self):
        self.login = self.ulogin.text()
        self.password = self.upassword.text()

        conn = connect_db(self.login, self.password)
        if self.login != 'administrator':
            self.parent.page_2.hide_admin_controls()
        elif self.login != 'manager' and self.login != 'administrator':
            self.parent.page_2.hide_add()
        if conn:  # если подключение прошло (логин и пароль правильный)
            self.parent.stackWidget.setCurrentIndex(1)
            self.parent.setWindowTitle('Главная')
            self.parent.setFixedSize(800, 600)
            self.parent.page_2.populate_table_combo(conn)
            conn.close()
        else:
            self.show_error_message("Неверный логин или пароль")
            self.upassword.clear()

    def show_error_message(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Ошибка авторизации")
        error_dialog.setText(message)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.exec_()

class BasicWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(BasicWindow, self).__init__()
        self.login = None
        self.password = None
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Initialize the table widget
        self.table_widget = QtWidgets.QTableWidget(self.central_widget)
        self.table_widget.setGeometry(10, 150, 750, 400)

        # Set horizontal scrollbar policy
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_widget.horizontalHeader().setStretchLastSection(False)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Name", "Age", "Address"])
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.add_row_button = QPushButton("Добавить строку", self.central_widget)
        self.add_row_button.setGeometry(10, 100, 250, 30)
        self.add_row_button.setStyleSheet("""
            QPushButton {
                border: 2px solid;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        self.add_row_button.clicked.connect(self.add_empty_row)
        self.edit_button = QPushButton("Изменить", self.central_widget)
        self.edit_button.setGeometry(270, 100, 250, 30)
        self.edit_button.setStyleSheet("""
            QPushButton {
                border: 2px solid;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        self.edit_button.clicked.connect(self.edit_row)
        self.delete_button = QPushButton("Удалить", self.central_widget)
        self.delete_button.setGeometry(530, 100, 250, 30)
        self.delete_button.setStyleSheet("""
            QPushButton {
                border: 2px solid;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        self.delete_button.clicked.connect(self.delete_row)
        self.refresh_button = QPushButton("Обновить", self.central_widget)
        self.refresh_button.setGeometry(250, 50, 100, 30)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 2px solid #2196F3;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        self.refresh_button.clicked.connect(self.populate_table)
        self.table_combo = QComboBox(self.central_widget)
        self.table_combo.activated[str].connect(self.fetch_data)
        self.table_combo.setGeometry(10, 50, 200, 30)
        self.combo_label = QLabel("Таблицы", self.central_widget)
        self.combo_label.setGeometry(80, 10, 80, 30)
        self.combo_label.setStyleSheet("font-weight: bold;")
        self.timer = QTimer()
        self.timer.timeout.connect(self.backup_database)

        # Create a menu bar
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setStyleSheet("""
                    QMenuBar {
                        background-color: #4CAF50;
                        color: white;
                        font-size: 12px;
                    }
                    QMenuBar::item {
                        background-color: #4CAF50;
                        color: white;
                    }
                    QMenuBar::item:selected {
                        background-color: #45a049;
                    }
                    QMenu {
                        background-color: #4CAF50;
                        color: white;
                        border: 1px solid #4CAF50;
                    }
                    QMenu::item:selected {
                        background-color: #45a049;
                    }
                """)
        self.setMenuBar(self.menu_bar)

        # Create a Backup menu
        backup_menu = self.menu_bar.addMenu("Бекап")

        # Add actions to the Backup menu
        backup_action = QAction("Бекап", self)
        backup_action.triggered.connect(self.backup_database)
        backup_menu.addAction(backup_action)

        auto_backup_action = QAction("Автоматический бекап", self)
        auto_backup_action.triggered.connect(self.show_backup_settings)
        backup_menu.addAction(auto_backup_action)

        # Create a Queries menu
        queries_menu = self.menu_bar.addMenu("Запросы")
        query_action = QAction("Выполнить запрос", self)
        query_action.triggered.connect(self.show_query_dialog)
        queries_menu.addAction(query_action)

    def show_query_dialog(self):
        dialog = QueryDialog(self)
        dialog.exec_()

    def show_backup_settings(self):
        dialog = BackupSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            interval = dialog.interval_spinbox.value() * 1000  # Convert to milliseconds
            self.timer.start(interval)
        else:
            self.timer.stop()

    def start_auto_backup(self):
        interval = self.interval_spinbox.value() * 1000
        self.timer.start(interval)

    def stop_auto_backup(self):
        self.timer.stop()

    def sort_table_by_column(self, column):
        current_order = self.sort_order.get(column, Qt.AscendingOrder)
        order = Qt.DescendingOrder if current_order == Qt.AscendingOrder else Qt.AscendingOrder
        self.sort_order[column] = order
        self.table_widget.horizontalHeader().setSortIndicator(column, order)
        self.table_widget.sortItems(column, order)

    def add_empty_row(self):
        column_names = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
        dialog = InputDialog(column_names, self)
        if dialog.exec_() == QDialog.Accepted:
            row_count = self.table_widget.rowCount()
            self.table_widget.insertRow(row_count)
            for col_number, input_field in enumerate(dialog.inputs):
                self.table_widget.setItem(row_count, col_number, QTableWidgetItem(input_field.text()))
            self.save_new_row(row_count)

    def save_new_row(self, row_number):
        row_data = [self.table_widget.item(row_number, col).text() if self.table_widget.item(row_number, col) else None for col in range(self.table_widget.columnCount())]
        conn = connect_db(self.login, self.password)
        try:
            if conn:
                cursor = conn.cursor()
                table_name = self.table_combo.currentText().strip()
                placeholders = ', '.join(['%s'] * len(row_data))
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"
                cursor.execute(query, row_data)
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {e}")
        finally:
            conn.close()

    def edit_row(self):
        if not self.table_combo.currentText():
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу из списка")
            return

        row_number = self.table_widget.currentRow()
        col_number = self.table_widget.currentColumn()

        if row_number < 0 and col_number < 0:
            return

        item = self.table_widget.item(row_number, col_number)

        dialog = QInputDialog()
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Edit Item")
        dialog.setLabelText("New Value:")
        dialog.setTextValue(item.text() if item else "")

        if dialog.exec_():
            new_value = dialog.textValue()
            self.table_widget.setItem(row_number, col_number, QTableWidgetItem(new_value))

            conn = connect_db(self.login, self.password)
            if conn:
                cursor = conn.cursor()
                table_name = self.table_combo.currentText().strip()
                cursor.execute(f"SELECT * FROM {table_name}")
                column_name = cursor.description[col_number][0]
                id_column = cursor.description[0][0]
                id_value = self.table_widget.item(row_number, 0).text()
                query = f"UPDATE {table_name} SET {column_name} = %s WHERE {id_column} = %s"
                cursor.execute(query, (new_value, id_value))
                conn.commit()
                conn.close()

    def delete_row(self):
        row_number = self.table_widget.currentRow()
        if row_number < 0:
            return
        conn = connect_db(self.login, self.password)
        if conn:
            cursor = conn.cursor()
            table_name = self.table_combo.currentText().strip()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            id_column = cursor.description[0][0]
            id_value = self.table_widget.item(row_number, 0).text()
            query = f"DELETE FROM {table_name} WHERE {id_column} = %s"
            cursor.execute(query, (id_value,))
            conn.commit()
            conn.close()
        self.table_widget.removeRow(row_number)

    def backup_database(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.sql"
        pg_dump_path = r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'
        os.environ['PGPASSWORD'] = '167943'
        command = [pg_dump_path, "--host=localhost", "--port=5432", "--username=postgres", "--dbname=bank", "--format=custom", "--file", backup_filename]
        subprocess.run(command)
        QMessageBox.warning(self, "Backup", "Успешное резервное копирование")

    def populate_table_combo(self, conn):
        self.table_combo.clear()
        table_names = get_table_names(conn)
        self.table_combo.addItems(table_names)

    def populate_table(self):
        self.table_widget.setRowCount(0)
        conn = connect_db(self.login, self.password)
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {self.table_combo.currentText()} ORDER BY 1 ASC')
        rows = cursor.fetchall()
        for row_index, row_data in enumerate(rows):
            self.table_widget.insertRow(row_index)
            for col_index, col_data in enumerate(row_data):
                self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(col_data)))
        cursor.close()
        conn.close()

    def fetch_data(self):
        if not self.table_combo.currentText():
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу из списка")
            return
        table_name = self.table_combo.currentText().strip()
        conn = connect_db(self.login, self.password)
        if conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1 ASC")
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(len(cursor.description))
            self.table_widget.setHorizontalHeaderLabels([i[0] for i in cursor.description])
            self.table_widget.horizontalHeader().setStretchLastSection(True)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row_number, row_data in enumerate(cursor.fetchall()):
                self.table_widget.insertRow(row_number)
                for col_number, data in enumerate(row_data):
                    self.table_widget.setItem(row_number, col_number, QTableWidgetItem(str(data)))
            conn.close()

    def hide_admin_controls(self):
        self.menu_bar.hide()

    def hide_add(self):
        self.edit_button.hide()
        self.delete_button.hide()
        self.add_row_button.hide()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('Авторизация')
        self.stackWidget = QtWidgets.QStackedWidget()
        layout = QtWidgets.QHBoxLayout(self.centralwidget)
        layout.addWidget(self.stackWidget)
        self.page_1 = LoginWindow(self)
        self.page_1.pushLog.clicked.connect(self.loga)
        self.stackWidget.addWidget(self.page_1)
        self.page_2 = BasicWindow()
        self.stackWidget.addWidget(self.page_2)

    def loga(self):
        if self.page_1.login and self.page_1.password:
            self.page_2.login = self.page_1.login
            self.page_2.password = self.page_1.password
            self.page_2.populate_table_combo(connect_db(self.page_1.login, self.page_1.password))
            self.stackWidget.setCurrentIndex(1)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
