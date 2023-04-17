import re
import ocrmypdf
import requests
from PyPDF2 import PdfReader
from datetime import datetime
from urllib.parse import urljoin
from pdfminer.layout import LAParams
from pdfminer.high_level import extract_text

from .enums import s, f


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
