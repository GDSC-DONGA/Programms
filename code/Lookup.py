import tkinter as tk
import firebase_admin
import sys
import traceback
import matplotlib.pyplot as plt
import ssl
import urllib.request
from tkinter import messagebox
from matplotlib import rc
import matplotlib
matplotlib.use('TkAgg')
from firebase_admin import credentials
from firebase_admin import db
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



path = <your key.json path>


cred = credentials.Certificate(path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://<your db name>.firebaseio.com/'
})

rc('font', family="Malgun Gothic")

def get_student_info(student_id):
    ref = db.reference(student_id)
    student = ref.get()
    if student:
        name = student.get("이름")
        scores = float(student.get("합계"))
        avg = float(student.get("평균"))
        return name, scores, avg
    else:
        return None, None, None


def get_students_info(student_id):
    ref = db.reference("students")
    students = ref.get()
    name = 0
    scores = 0.0
    if students:
        total = 0.0
        count = 0.0
        for student_key, student in students.items():
            if student_key == student_id:
                name = student.get("이름")
                scores = student.get("합계")
            total += sum(student.get("합계"))
            count += len(student.get("이름"))
        avg = total / count
        return name, scores, total, avg
    else:
        return None, None, None, None


def show_student_info(event=None):
    student_id = entry.get()
    try:
        name, scores, avg = get_student_info(student_id)
        if 'canvas' in globals():
            canvas.get_tk_widget().destroy()
        if name:
            name_label.config(text=f"이름: {name}")
            scores_label.config(text=f"합계: {scores}")
            avg_label.config(text=f"평균: {round(avg, 3)}")
            draw_chart(name, scores, avg)
        else:
            name_label.config(text="")
            scores_label.config(text="")
            avg_label.config(text="학번에 해당하는 학생을 찾을 수 없습니다.")
    except Exception as e:
        print(e)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_list)
        with open("error_log.txt", "a") as f:
            f.write(tb_str)
        messagebox.showerror("Error", "예기치 못한 에러가 발생했습니다.")


def on_closing():
    plt.close()
    root.destroy()


def draw_chart(name, scores, avg):
    ref = db.reference()
    students = ref.get()

    global canvas

    if students:
        all_scores = []
        all_avgs = []
        for student_key, student in students.items():
            if student_key != 'admin':
                all_scores.append(float(student.get("합계")))
                all_avgs.append(float(student.get("평균")))
        all_total = sum(all_scores) / len(all_scores)  # 합계 평균
        all_avg = sum(all_avgs) / len(all_scores)  # 전체 평균

        fig, ax = plt.subplots()
        bars = ax.bar(["Your Scores", "Your Average", "All Scores avg", "All Average"],
                      [float(scores), float(avg), all_total, all_avg],
                      color=["red", "red", "blue", "blue"])

        ax.set_title(f"{name}'s Scores")
        ax.set_ylabel('Scores')
        ax.set_ylim([0, max(all_total, max(float(scores), float(avg))) + 10])

        # 막대 위에 값 추가
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, round(float(height), 3),
                    ha='center', va='bottom')

        # 범례 추가
        legend_labels = ["Your Scores", "Your Average", "All Scores avg", "All Average"]
        legend_handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ["red", "red", "blue", "blue"]]
        ax.legend(legend_handles, legend_labels)

        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        canvas.get_tk_widget().pack()


# GUI 구성
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

root = tk.Tk()

url = "https://raw.githubusercontent.com/GDSC-DONGA/Programms/main/icon/gdsc-logo.ico"
icon_path = "icon.ico"
urllib.request.urlretrieve(url, icon_path)
# icon_path = "icon.ico"
# # wget.download(url, out=icon_path)
root.iconbitmap(icon_path)
root.configure(bg="white")
root.title("GDSC DAU 포인트 조회 시스템")
info_label = tk.Label(root, text="GDSC-DAU 포인트 조회 시스템입니다.\n학번을 입력하여 본인의 포인트를 조회하고 전체와 비교해보세요!", bg="white")
info_label.pack()

entry_label = tk.Label(root, text="학번 입력:", bg="white")
entry_label.pack()
entry = tk.Entry(root, bg="white")
entry.pack()
entry.bind("<Return>", show_student_info)

button = tk.Button(root, text="검색", command=show_student_info, bg="white")
button.pack()

name_label = tk.Label(root, text="", bg="white")
name_label.pack()

scores_label = tk.Label(root, text="", bg="white")
scores_label.pack()

avg_label = tk.Label(root, text="", bg="white")
avg_label.pack()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
