import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QTableWidget, QTableWidgetItem, \
    QMessageBox
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

            # 파일 저장
            wb.save(f"{self.parent.filename}.xlsx")
            self.parent.first_ref = db.reference()
            # 파이어베이스에 결과물 저장
            for row in range(0, self.parent.table_widget.rowCount()):
                student_number = self.parent.table_widget.item(row, 0).text()
                print(student_number, end=' ')
                name = self.parent.table_widget.item(row, 1).text()
                total = self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 2).text()
                average = self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 1).text()
                self.parent.first_ref.child(student_number).set({
                    "이름": name,
                    "합계": total,
                    "평균": average
                })
                print(name)

            self.parent.second_ref = db.reference("/admin")
            # 파이어베이스에 결과물 저장
            second_param = {}
            for row in range(self.parent.table_widget.rowCount()):
                student_number = self.parent.table_widget.item(row, 0).text()
                print(student_number, end=' ')
                second_param = {
                    "이름": self.parent.table_widget.item(row, 1).text(),
                    "공부인증챌린지": self.parent.table_widget.item(row, 2).text(),
                    'ZEP DAILY 모각공': self.parent.table_widget.item(row, 3).text(),
                    '설문조사참여': self.parent.table_widget.item(row, 4).text(),
                    '열품타': self.parent.table_widget.item(row, 5).text(),
                    'DAU 아이디어 톤': self.parent.table_widget.item(row, 6).text(),
                    '조력자설문(이월)': self.parent.table_widget.item(row, 7).text(),
                    'ZEP제작': self.parent.table_widget.item(row, 8).text(),
                    '게임기획': self.parent.table_widget.item(row, 9).text(),
                    "합계": self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 2).text(), # 포인트 항목 추가를 고려해 인덱스 설정함.
                    "평균": self.parent.table_widget.item(row, self.parent.table_widget.columnCount() - 1).text(),
                }
                self.parent.second_ref.child(student_number).set(second_param)
                print(second_param["이름"])

        except Exception as e:
            print(e)
            self.finished_signal.emit(False)
        else:
            self.finished_signal.emit(True)


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

        self.filename = "멤버 포인트 보드"
        self.data = []

        # Firebase 프로젝트에 액세스하는 코드
        first_path = <your key.json path>
        first_cred = credentials.Certificate(first_path)
        self.first_firebase_app = firebase_admin.initialize_app(first_cred, {
            'databaseURL': 'https://<your db name>.firebaseio.com/'
        })

        self.table_widget.itemChanged.connect(self.update_total_and_average)  # itemChanged 시그널 연결
        self.show()

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

    def open_file_dialog(self):
        self.table_widget.clear()
        ref = db.reference('/admin')
        students = ref.order_by_child('이름').get()
        students_number = list(students.keys())

        for key, value in students.items():
            print(key, value)

        if students is not None:
            headers = ['학번', '이름', '공부인증챌린지', 'ZEP DAILY 모각공', '설문조사참여', '열품타', 'DAU 아이디어 톤', '조력자설문(이월)', 'ZEP제작',
                       '게임기획', '합계', '평균']
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
        del item

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
        self.filename, _ = QFileDialog.getSaveFileName(self, "파일 저장", "",
                                                       "Excel Files (*.xlsx);;CSV Files (*.csv)", options=options)
        if self.filename:
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


'''
pyinstaller --noconfirm --onefile --noconsole --icon "C:/Users/pwjdg/PycharmProjects/pythonProject2/gdsc-logo.ico" --name "GDSC DAU 멤버 포인트 관리자"  "C:/Users/pwjdg/PycharmProjects/pythonProject2/PointManager.py"

'''