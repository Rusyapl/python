import datetime
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QApplication, QMessageBox, QLineEdit, QPushButton, QComboBox, \
    QLabel, QInputDialog, QFileDialog, QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView, QTableWidget
import psycopg2
from PyQt5.QtCore import Qt
import subprocess
import os

def connect_db(login, password):
    try:
        conn = psycopg2.connect(
            dbname="rusya",
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
    def __init__(self, column_count, parent=None):
        super(InputDialog, self).__init__(parent)

        self.setWindowTitle("Введите данные")
        self.layout = QFormLayout(self)

        self.inputs = []
        for i in range(column_count):
            label = QLabel(f"Поле {i + 1}:")
            line_edit = QLineEdit()
            self.layout.addRow(label, line_edit)
            self.inputs.append(line_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.layout.addRow(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

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

        self.pushLog = QPushButton('Авторизация')
        self.pushLog.clicked.connect(self.loga)

        formlayout = QtWidgets.QFormLayout(self.centralwidget)
        formlayout.addRow('Введите логин', self.ulogin)
        formlayout.addRow('Введите пароль', self.upassword)
        formlayout.addRow('', self.pushLog)

    def check_time(self):
        current_time = datetime.datetime.now().time()
        if current_time < datetime.time(8) or current_time >= datetime.time(20):
            msg = QMessageBox()
            msg.setWindowTitle("Ошибка входа")
            msg.setText("Вход разрешен только с 8 утра до 8 вечера")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()
            raise Exception('Вход разрешен только с 8 утра до 8 вечера')

    def loga(self):
        self.check_time()
        self.login = self.ulogin.text()
        self.password = self.upassword.text()

        conn = connect_db(self.login, self.password)
        if conn:
            self.parent.stackWidget.setCurrentIndex(1)
            self.parent.setWindowTitle('Главная')
            self.parent.setFixedSize(800, 600)
            self.parent.page_2.populate_table_combo(conn)
            conn.close()
        else:
            self.show_error_message("Неверный логин или пароль")
            self.upassword.clear()

        if self.login == 'user1' and self.password == 'pass1' or self.login == 'user4' and self.password == 'pass4' or self.login == 'user5' and self.password == 'pass5':
            self.parent.page_2.another_combo.hide()
            self.parent.page_2.another_label.hide()
            self.parent.page_2.zakaz_button.hide()
            self.parent.page_2.edit_button.hide()
            self.parent.page_2.delete_button.hide()
            self.parent.page_2.add_row_button.hide()
            self.parent.page_2.backup_button.hide()
        elif self.login == 'user2' and self.password == 'pass2':
            self.parent.page_2.another_combo.hide()
            self.parent.page_2.another_label.hide()
            self.parent.page_2.backup_button.hide()

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

        # Set central widget
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.table_widget = QtWidgets.QTableWidget(self.central_widget)
        self.table_widget.setGeometry(10, 100, 750, 400)

        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Name", "Age", "Address"])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.add_row_button = QPushButton("Добавить строку", self.central_widget)
        self.add_row_button.setGeometry(10, 520, 100, 30)
        self.add_row_button.clicked.connect(self.add_empty_row)

        self.edit_button = QPushButton("Изменить", self.central_widget)
        self.edit_button.setGeometry(120, 520, 100, 30)
        self.edit_button.clicked.connect(self.edit_row)

        self.delete_button = QPushButton("Удалить", self.central_widget)
        self.delete_button.setGeometry(230, 520, 100, 30)
        self.delete_button.clicked.connect(self.delete_row)

        self.zakaz_button = QPushButton('Сделать заказ', self.central_widget)
        self.zakaz_button.setGeometry(340, 520, 100, 30)
        self.zakaz_button.clicked.connect(self.call_zakaz)

        self.refresh_button = QPushButton('Обновить', self.central_widget)
        self.refresh_button.setGeometry(450, 520, 100, 30)
        self.refresh_button.clicked.connect(self.populate_table)

        self.table_combo = QComboBox(self.central_widget)
        self.table_combo.activated[str].connect(self.fetch_data)
        self.table_combo.setGeometry(10, 50, 200, 30)

        self.another_combo = QComboBox(self.central_widget)
        self.another_combo.activated[str].connect(self.execute_query)
        self.another_combo.setGeometry(220, 50, 200, 30)

        self.combo_label = QLabel("Функционал:", self.central_widget)
        self.combo_label.setGeometry(10, 10, 80, 30)
        self.combo_label.setStyleSheet("font-weight: bold;")

        self.another_label = QLabel("Дополнительно:", self.central_widget)
        self.another_label.setGeometry(220, 10, 180, 30)
        self.another_label.setStyleSheet("font-weight: bold;")

        self.backup_button = QPushButton('Резервное копирование', self.central_widget)
        self.backup_button.setGeometry(620, 520, 160, 30)
        self.backup_button.clicked.connect(self.backup_database)

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table_by_column)

    def sort_table_by_column(self, column):
        current_order = self.table_widget.horizontalHeader().sortIndicatorOrder()
        if current_order == Qt.AscendingOrder:
            order = Qt.DescendingOrder
        else:
            order = Qt.AscendingOrder

        self.table_widget.horizontalHeader().setSortIndicator(column, order)
        self.table_widget.sortItems(column, order)

    def call_zakaz(self):
        conn = connect_db(self.login, self.password)
        cursor = conn.cursor()

        try:
            cursor.execute('CALL zakaz()')
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Заказ сделан')
        except Exception as e:
            print (e)
            if str(e) == "Товар в полном наличие":  # replace this with your actual error message
                QMessageBox.critical(self, 'Ошибка', 'Товар в полном наличие')
            else:
                QMessageBox.critical(self, 'Ошибка', 'Товар в полном наличие')

        cursor.close()
        conn.close()

    def add_empty_row(self):
        dialog = InputDialog(self.table_widget.columnCount(), self)
        if dialog.exec_() == QDialog.Accepted:
            row_count = self.table_widget.rowCount()
            self.table_widget.insertRow(row_count)
            for col_number, input_field in enumerate(dialog.inputs):
                self.table_widget.setItem(row_count, col_number, QTableWidgetItem(input_field.text()))

            self.save_new_row(row_count)

    def save_new_row(self, row_number):
        row_data = []
        column_count = self.table_widget.columnCount()
        for col in range(column_count):
            item = self.table_widget.item(row_number, col)
            if item is not None:
                row_data.append(item.text())
            else:
                row_data.append(None)

        conn = connect_db(self.login, self.password)
        try:
            if conn:
                cursor = conn.cursor()
                table_name = self.table_combo.currentText().strip()

                placeholders = ', '.join(['%s'] * len(row_data))
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"
                cursor.execute(query, row_data)

                conn.commit()
                conn.close()
        except Exception as e:
            msg = QMessageBox()
            msg.setWindowTitle("Ошибка ввода")
            msg.setText("Ошибка ввода данных")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()

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

        # Delete the row from the QTableWidget
        self.table_widget.removeRow(row_number)

    def backup_database(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.sql"
        pg_dump_path = f'C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe'
        #command = f' —host=127.0.0.1 —port=5432 —username=postgres —dbname=rusya —format=custom —file={backup_filename}'
        os.environ['PGPASSWORD'] = '123'
        command = [pg_dump_path,
                   f"--host=localhost",
                   f"--port=5432",
                   f"--username=postgres",
                   f"--dbname=rusya",
                   "--format=custom",
                   "--file", backup_filename]
        subprocess.run(command, shell=True)

        # "pg_dump —host=127.0.0.1 —port=5432 —username=postgres —dbname=rusya —format=custom —file=C:\Games\pythonProject14\Rusya\BSBD.backup"
    def restore_database(backup_file, port="5432"):
        try:

        # Full path to pg_restore, adjust if needed
            pg_restore_path = "C:/Program Files/PostgreSQL/16/bin/pg_restore.exe"  # Example path for Windows

            # Setting the PGPASSWORD environment variable to handle password
            os.environ['PGPASSWORD'] = "1234"

            # Construct the command
            command = [pg_restore_path,
                       f"--host='localhost'",
                       f"--port=5432",
                       f"--username='postgres'",
                       f"--dbname='rusya'",
                       "--format=custom",
                       "--clean",  # Clean (drop) existing objects before restore
                       "--if-exists",  # Ignore errors if objects do not exist
                       backup_file]

            # Execute the command
            subprocess.run(command, check=True)

            return True  # Return True if restore succeeds
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False

    # "pg_restore —host=127.0.0.1 —port=5432 —username=Admin —dbname=postgres —no-owner —no-privileges —clean —if-exists C:\Users\sasha\PycharmProjects\pythonProject1\postgres_backup.backup"

    def populate_table_combo(self, conn):
        self.table_combo.clear()
        table_names = get_table_names(conn)
        self.table_combo.addItems(table_names)

        self.another_combo.clear()
        self.another_combo.addItem("Вывести все товары из отдела 'Консервы'")
        self.another_combo.addItem("Список просроченных товаров")
        self.another_combo.addItem("Количество товаров молочного ассортимента")
        self.another_combo.addItem("Товары по цене меньше 30 руб")
        self.another_combo.addItem("Количество покупателей за последние 2 дня")
        self.another_combo.addItem("Товары, которых осталось на прилавках меньше 10% от товара с максимальным количеством")
        self.another_combo.addItem("Продукты, поставленные за последний месяц")
        self.another_combo.addItem("Покупатели, поставившие оценку выше 4")

    def populate_table(self):
        self.table_widget.setRowCount(0)

        # Connect to the database
        conn = connect_db(self.login, self.password)
        cursor = conn.cursor()

        # Get the name of the first column
        cursor.execute(f'SELECT * FROM {self.table_combo.currentText()} LIMIT 1')
        first_column = cursor.description[0][0]

        # Execute a SELECT query to retrieve the data, ordered by the first column
        cursor.execute(f'SELECT * FROM {self.table_combo.currentText()} ORDER BY {first_column} ASC')
        rows = cursor.fetchall()

        # Add the data to the table
        for row_index, row_data in enumerate(rows):
            self.table_widget.insertRow(row_index)
            for col_index, col_data in enumerate(row_data):
                self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(col_data)))

        # Close the database connection
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

    def execute_query(self):
        query = ""
        if self.another_combo.currentText() == "Вывести все товары из отдела 'Консервы'":
            query = """
                    SELECT id_tovara, name_tovara
                    FROM tovari
                    INNER JOIN otdeli ON tovari.id_otdela = otdeli.id_otdela AND otdeli.name_otdela = 'Консервы';
                """
        elif self.another_combo.currentText() == "Список просроченных товаров":
            query = """
                    SELECT tovari.id_tovara, tovari.name_tovara, postavka.production_date, postavka.expiry_date
                    FROM tovari
                    INNER JOIN postavka ON postavka.id_tovara = tovari.id_tovara AND postavka.expiry_date <= CURRENT_TIMESTAMP;
                """
        elif self.another_combo.currentText() == "Количество товаров молочного ассортимента":
            query = """
                    SELECT COUNT (*)
                    FROM tovari
                    INNER JOIN otdeli ON otdeli.id_otdela = tovari.id_otdela and otdeli.name_otdela like 'Молочный';

                """
        elif self.another_combo.currentText() == "Товары по цене меньше 30 руб":
            query = """
                    SELECT tovari.name_tovara, cost_1 FROM tovari
                    INNER JOIN postavka ON postavka.id_tovara = tovari.id_tovara and postavka.cost_1 < 30;
                """
        elif self.another_combo.currentText() == "Количество покупателей за последние 2 дня":
            query = """
                    select count (*) from pokupateli
                    inner join prodaji on pokupateli.id_pokupatelya = prodaji.id_pokupatelya and prodaji.date_prodaji > NOW() - INTERVAL '2' DAY;
                """
        elif self.another_combo.currentText() == "Товары, которых осталось на прилавках меньше 10% от товара с максимальным количеством":
            query = """
                    WITH Максимум_товара AS (
                    SELECT MAX(count_tovara) AS Максимальное_количество
                    FROM postavka
                    )

                    SELECT tovari.name_tovara, postavka.count_tovara - prodaji.count_tovara as Разница, Максимум_товара.Максимальное_количество
                    FROM tovari
                    INNER JOIN postavka ON postavka.id_tovara = tovari.id_tovara
                    INNER JOIN prodaji ON prodaji.id_postavki = postavka.id_postavki
                    CROSS JOIN Максимум_товара
                    WHERE (postavka.count_tovara - prodaji.count_tovara) < (Максимум_товара.Максимальное_количество / 10)
                    GROUP BY tovari.name_tovara, postavka.count_tovara, prodaji.count_tovara, Максимум_товара.Максимальное_количество
                """
        elif self.another_combo.currentText() == "Продукты, поставленные за последний месяц":
            query = """
                    select * from tovari
                    inner join postavka on tovari.id_tovara = postavka.id_tovara and date_postavki > NOW() - INTERVAL '30' DAY
                    order by tovari.id_tovara
                """
        elif self.another_combo.currentText() == "Покупатели, поставившие оценку выше 4":
            query = """
                   select pokupateli.id_pokupatelya, pokupateli.Surname, reviews.Ball 
                    from pokupateli
                    inner join prodaji on prodaji.id_pokupatelya = pokupateli.id_pokupatelya
                    inner join reviews on prodaji.id_prodaji = reviews.id_prodaji and reviews.Ball > 4
                    order by pokupateli.id_pokupatelya, reviews.Ball
                """

        if self.login == 'user3' and self.password == 'pass3' or self.login == 'user2' and self.password == 'pass2':
            conn = connect_db(self.login, self.password)
            if conn:
                cursor = conn.cursor()
                cursor.execute(query)

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
