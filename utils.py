import xlsxwriter
import os
from datetime import datetime 

def create_excel_file(filename, data, dir):
    workbook = xlsxwriter.Workbook(f'./{dir}/{filename}.xlsx')
    worksheet = workbook.add_worksheet('Comments')
    row = 0
    id = 0
    for item in data:
        worksheet.write(row, 0, id)
        worksheet.write(row, 1, item)
        row += 1
        id += 1
    workbook.close()

def create_directory():
    now = datetime.now()
    name = now.strftime("%Y-%m-%d %H-%M-%S")
    os.mkdir(name)
    return name
