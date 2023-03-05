import json
import sys
import time
import traceback
import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QTableWidget, QTableWidgetItem, \
    QMessageBox, QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal, QMutexLocker, QReadWriteLock, QReadLocker, QMutex
from openpyxl import load_workbook, Workbook
import firebase_admin
from firebase_admin import credentials, db


class SaveFileThread(QThread):
    finished_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mutex = QMutex()

    def run(self):
        try:
            wb = Workbook()
            ws = wb.active

            # row 해더 추가
            headers = self.parent.table_widget.horizontalHeaderItem(0).text()
            for col in range(1, self.parent.table_widget.columnCount()):
                headers += "\t" + self.parent.table_widget.horizontalHeaderItem(col).text()
            ws.append(headers.split("\t"))

            # row 데이터 추가

            self.parent.data = []
            total_count = self.parent.table_widget.rowCount() - 1
            for row in range(self.parent.table_widget.rowCount()):
                row_data = []
                for col in range(self.parent.table_widget.columnCount()):
                    with QMutexLocker(self.mutex):
                        item = self.parent.table_widget.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                with QMutexLocker(self.mutex):
                    self.parent.data.append(row_data)
                    ws.append(row_data)

            self.parent.first_ref = db.reference()
            # 파이어베이스에 결과물 저장
            for row in range(0, self.parent.table_widget.rowCount()):
                student_number = self.parent.table_widget.item(row, 0).text()
                # print(student_number, end=' ')
                name = self.parent.table_widget.item(row, 1).text()
                total = self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 2).text()
                average = self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 1).text()
                self.parent.first_ref.child(student_number).set({
                    "이름": name,
                    "합계": total,
                    "평균": average
                })
                # print(name)

            self.parent.second_ref = db.reference("/admin")
            # 파이어베이스에 결과물 저장
            second_param = {}
            for row in range(self.parent.table_widget.rowCount()):
                student_number = self.parent.table_widget.item(row, 0).text()
                # print(student_number, end=' ')

                for col in range(1, self.parent.table_widget.columnCount()):
                    column_name = self.parent.table_widget.horizontalHeaderItem(col).text()
                    cell_value = self.parent.table_widget.item(row, col).text()
                    second_param[column_name] = cell_value
                self.parent.second_ref.child(student_number).set(second_param)
                # print(second_param)

        except Exception as e:
            # print(e)
            self.finished_signal.emit(False)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_str = ''.join(tb_list)
            with open("error_log.txt", "a") as f:
                f.write(tb_str)
        else:
            self.finished_signal.emit(True)

            # 저장 후 백업
            backup = self.parent.first_ref.get()
            with open(f"saved_{self.parent.backup_filename}", 'w') as f:
                json.dump(backup, f)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.save_thread = None
        self.setWindowTitle("GDSC DAU 멤버 포인트 관리 시스템")
        self.setGeometry(100, 100, 1250, 1200)

        self.table_widget = QTableWidget()
        self.setCentralWidget(self.table_widget)

        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        self.open_file_action = QAction("Open File", self)
        self.open_file_action.triggered.connect(self.open_file_dialog)
        self.file_menu.addAction(self.open_file_action)

        self.save_file_action = QAction("Save File", self)
        self.save_file_action.triggered.connect(self.save_file_dialog)
        self.file_menu.addAction(self.save_file_action)

        self.add_column_action = QAction("Add Column", self)  # new
        self.add_column_action.triggered.connect(self.add_column)
        self.file_menu.addAction(self.add_column_action)

        self.filename = "멤버 포인트 보드"
        self.data = []
        self.column_names = []  # 기본 열 이름 설정
        # Firebase 프로젝트에 액세스하는 코드
        first_path = {json file path}
        first_cred = credentials.Certificate(first_path)
        self.first_firebase_app = firebase_admin.initialize_app(first_cred, {
            'databaseURL': 'https://<RDB url>.firebaseio.com/'
        })

        self.table_widget.itemChanged.connect(self.update_total_and_average)  # itemChanged 시그널 연결
        self.show()

        # 백업 날짜 지정
        self.now = datetime.datetime.now()
        self.date_str = self.now.strftime("%Y-%m-%d")
        self.backup_filename = f"{self.date_str}_backup.json"

    def update_total_and_average(self, item):
        if item is not None and 2 <= item.column() < self.table_widget.columnCount() - 2:
            # 2번째 열 이후로 처리
            total = 0
            count = self.table_widget.columnCount() - 4  # 합계를 계산할 열의 개수 (8개)
            for col in range(2, self.table_widget.columnCount() - 2):  # 2번째 열부터 총합 계산
                cell_value = self.table_widget.item(item.row(), col)
                if cell_value is not None and cell_value.text().isnumeric():
                    total += int(cell_value.text())

            # 합계 열 갱신
            total_item = QTableWidgetItem(str(total))
            self.table_widget.setItem(item.row(), self.table_widget.columnCount() - 2, total_item)

            # 평균 열 갱신
            average_item = QTableWidgetItem(str(total / count))
            self.table_widget.setItem(item.row(), self.table_widget.columnCount() - 1, average_item)

    def add_column(self):
        # get the current number of columns
        current_column_count = self.table_widget.columnCount()

        # get the name of the new column from the user
        column_name, ok = QInputDialog.getText(self, 'Add Column', '새로운 항목 이름을 입력하세요:')

        if ok and column_name.strip() != "":
            self.column_names.insert(-2, column_name)  # 열 이름 리스트 업데이트
            header_item = QTableWidgetItem(column_name)
            index = current_column_count - 2
            self.table_widget.insertColumn(index)
            self.table_widget.setHorizontalHeaderItem(index, header_item)
            # print(self.column_names)

            # add empty cells to the new column for each row
            for row in range(self.table_widget.rowCount()):  # 0으로 초기화
                item = QTableWidgetItem("0")
                self.table_widget.setItem(row, index, item)

    def open_file_dialog(self):
        self.table_widget.clear()

        # 백업용
        dump = db.reference('')
        dump_data = dump.get()


        # 파일 백업
        with open(self.backup_filename, 'w') as f:
            json.dump(dump_data, f)

        ref = db.reference('/admin')
        students = ref.order_by_child('이름').get()
        students_number = list(students.keys())
        # print(students_number[0])
        left_header = ['학번', '이름']
        right_header = ['합계', '평균']
        student_feature = None

        for student_number in students_number:
            student_feature = students[student_number]

        headers = list(student_feature.keys())

        to_remove = ["합계", "평균", "이름"]

        # 리스트에서 해당 열 이름을 가진 원소를 삭제
        for col_name in to_remove:
            headers.remove(col_name)

        # sum
        headers = left_header + headers + right_header
        # print(headers)

        # key value 확인
        # for key, value in students.items():
        #     print(key, value)

        if students is not None:

            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setRowCount(len(students))

            self.table_widget.setHorizontalHeaderLabels(headers)

            for row, student in enumerate(students.values()):
                data_row = []
                for col, header in enumerate(headers):
                    if header == '학번':
                        cell_value = list(students.keys())[row]
                    else:
                        cell_value = student.get(header)
                        if cell_value is None:
                            cell_value = 0
                    item = QTableWidgetItem(str(cell_value))
                    self.table_widget.setItem(row, col, item)
                    data_row.append(cell_value)
                self.data.append(data_row)

        # 합계와 평균을 업데이트
        self.update_total_and_average(None)

        del headers
        del data_row

    def save_file_dialog(self):
        # Check if there is any data to save
        if self.table_widget.rowCount() == 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("저장할 데이터가 없습니다.")
            msg_box.setWindowTitle("Save File")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        QMessageBox.information(self, "파일 저장", "작업이 끝내면 안내하겠습니다.")
        self.save_thread = SaveFileThread(parent=self)
        self.save_thread.finished_signal.connect(self.show_save_file_dialog)
        self.save_thread.start()

        # time.sleep(10)
        # del self.save_thread

    def show_save_file_dialog(self, success):
        if success:
            QMessageBox.information(self, "파일 저장", "파일이 저장되었습니다.")
        else:
            QMessageBox.critical(self, "파일 저장", "파일 저장 중 오류가 발생했습니다.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    app.exec_()
