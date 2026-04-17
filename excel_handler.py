import openpyxl
import os
from datetime import datetime

EXCEL_FILE = "students.xlsx"


def init_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"
        ws.append(["Name", "Email", "Phone", "Course", "Date"])
        wb.save(EXCEL_FILE)
        print("Excel file created!")


def save_student(name: str, email: str, phone: str, course: str):
    init_excel()
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([
        name,
        email,
        phone,
        course,
        datetime.now().strftime("%d-%m-%Y %H:%M")
    ])
    wb.save(EXCEL_FILE)
    print(f"Student saved: {name}")


if __name__ == "__main__":
    init_excel()
    save_student("Test Student", "test@gmail.com", "+919999999999", "Python")
    print("Excel test success!")
