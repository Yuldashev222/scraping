import os
import re
import zipfile
import ocrmypdf
import subprocess
from PyPDF2 import PdfReader
from datetime import datetime

from .enums import s, f
from .tasks import detect_pdfs


def convert_word_to_pdf(doc_path, path):
    if not doc_path:
        return
    subprocess.call(['soffice', '--convert-to', 'pdf', '--outdir', path, doc_path])
    return doc_path


def extract_zip_file(zip_file_location, pk):
    with zipfile.ZipFile(zip_file_location, 'r') as file_zip:
        zip_file_dir = os.path.join(
            os.path.dirname(zip_file_location),
            zip_file_location[:str(zip_file_location).rindex('.')]
        )
        if not os.path.exists(zip_file_dir):
            os.makedirs(zip_file_dir)
        file_zip.extractall(zip_file_dir)
        detect_pdfs.delay(zip_file_dir, pk)


def file_upload_location(obj, file):
    return f'{obj.country}/{obj.region}/test/{file}'


def myocr(input_file):
    ocrmypdf.ocr(
        input_file, input_file, output_type='pdfa',
        rotate_pages=True, deskew=True, language='swe', skip_text=True
    )


def get_text_and_pages(pdf_file):
    myocr(pdf_file)
    print('GET TEXT ========')
    with open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        pages = len(pdf_reader.pages)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
    text = ' '.join(text.split()).strip().replace("\x00", "\uFFFD").lower()
    print('COMPLETED=====================')
    return text, pages


def get_date_from_text(text):
    date_pattern = r'((\d{4}|\d{2}) ?- ?(0[1-9]|1[012]) ?- ?(0[1-9]|[12][0-9]|3[01]))|((\d{4}|\d{2}) ?(0[1-9]|1[012]) ?(0[1-9]|[12][0-9]|3[01]))'
    date = re.search(date_pattern, text)
    if bool(date):
        date = ''.join(date.group().split()).replace('-', '')
        try:
            if len(date) == 6:
                date = datetime.strptime(date, '%y%m%d')
            else:
                date = datetime.strptime(date, '%Y%m%d')
        except ValueError:
            return False
        if date > datetime.now():  # last
            return False
        return date.date()
    return False


def get_organ_from_text(text):
    if s in text and f in text:
        return 's' if text.index(s) < text.index(f) else 'f'
    elif s in text:
        return 's'
    elif f in text:
        return 'f'
    return False


def is_ignore_file(text, ignore_texts):
    if [word for word in ignore_texts if word in text]:
        return True
    return False
