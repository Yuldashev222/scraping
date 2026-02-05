import os
import re
import uuid
import zipfile
import ocrmypdf
import subprocess
from PyPDF2 import PdfReader
from datetime import datetime
from django.utils.timezone import now

from .enums import exact_words, Organ
from .tasks import detect_pdfs


def convert_word_to_pdf(doc_path, path):
    if not doc_path:
        return
    subprocess.call(['soffice', '--convert-to', 'pdf', '--outdir', path, doc_path])
    return doc_path


def extract_zip_file(zip_file_location, pk):
    with zipfile.ZipFile(zip_file_location, 'r') as file_zip:
        filename_no_ext = os.path.splitext(os.path.basename(zip_file_location))[0]
        filename = f'{filename_no_ext}_{uuid.uuid4()}'
        zip_file_dir = os.path.join(
            os.path.dirname(zip_file_location),
            filename
        )
        os.makedirs(zip_file_dir)
        file_zip.extractall(zip_file_dir)
        detect_pdfs.delay(zip_file_dir, pk)


def file_upload_location(obj, file):
    return f'{obj.country}/{obj.region}/test/{file}'


def myocr(input_file):
    ocrmypdf.ocr(input_file=input_file,
                 output_file=input_file,
                 deskew=True,
                 output_type='pdf',
                 language='swe',
                 skip_text=True)


def is_desired_date(date):
    today = now().date()
    now_month = today.month
    return True if date >= now().date().replace(month=now_month - 2, day=1) else False


def get_pages_text(pdf_file, pages=3):
    text = ''
    if pages > 0:
        temp = '1' if pages == 1 else f'1-{pages}'
        ocrmypdf.ocr(input_file=pdf_file, output_file=pdf_file + '.first_page.pdf', deskew=True, output_type='pdf',
                     language='swe', skip_text=True, pages=temp)

        with open(pdf_file + '.first_page.pdf', 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in range(pages):
                try:
                    text += pdf_reader.pages[page].extract_text()
                except IndexError:
                    break
            text = ' '.join(text.split()).strip().lower()
    return text


def get_text_and_pages(pdf_file):
    text = ''
    myocr(pdf_file)
    print('GET TEXT ========')
    with open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        pages = len(pdf_reader.pages)
        for page in pdf_reader.pages:
            text += page.extract_text()
    text = ' '.join(text.split()).strip().lower()
    print('COMPLETED=====================')
    return text, pages


swedish_to_english_months = {
    'Januari': 'January',
    'januari': 'January',
    'Jan': 'January',
    'jan': 'January',
    'Februari': 'February',
    'februari': 'February',
    'Feb': 'February',
    'feb': 'February',
    'Mars': 'March',
    'mars': 'March',
    'Mar': 'March',
    'mar': 'March',
    'April': 'April',
    'april': 'April',
    'Apr': 'April',
    'apr': 'April',
    'Maj': 'May',
    'maj': 'May',
    'Juni': 'June',
    'juni': 'June',
    'Jun': 'June',
    'jun': 'June',
    'Juli': 'July',
    'juli': 'July',
    'Jul': 'July',
    'jul': 'July',
    'Augusti': 'August',
    'augusti': 'August',
    'Aug': 'August',
    'aug': 'August',
    'September': 'September',
    'september': 'September',
    'Sep': 'September',
    'sep': 'September',
    'Oktober': 'October',
    'oktober': 'October',
    'Okt': 'October',
    'okt': 'October',
    'November': 'November',
    'november': 'November',
    'Nov': 'November',
    'nov': 'November',
    'December': 'December',
    'december': 'December',
    'Dec': 'December',
    'dec': 'December'
}


def get_date_from_text(text, ignore_file=False, first_date=False):
    date_pattern = (r'(\d{4} ?(-|‐) ?(0[1-9]|1[012]) ?(-|‐) ?(0[1-9]|[12][0-9]|3[01]))'
                    r'|'
                    r'((0[1-9]|[12][0-9]|3[01])( .|.|. | . )(0[1-9]|1[012])( .|.|. | . )\d{4})'
                    r'|'
                    r'((0?[1-9]|[12][0-9]|3[01]) ?'
                    r'(Januari|januari|Jan|jan|Februari|februari|Feb|feb|Mars|mars|Mar|mar|April|april|Apr|apr|Maj|maj|Juni|juni|Jun|jun|Juli|juli|Jul|jul|Augusti|augusti|Aug|aug|September|september|Sep|sep|Oktober|oktober|Okt|okt|November|november|Nov|nov|December|december|Dec|dec)'
                    r' ?\d{4})')
    date = re.search(date_pattern, text)
    if bool(date):
        temp = date.group()
        date = date.group().replace(' ', '').replace('-', '').replace('‐', '')
        try:
            if date.isdigit():
                date = datetime.strptime(date, '%Y%m%d')
            elif '.' in date:
                date = datetime.strptime(date, '%d.%m.%Y')
            else:
                val = list(swedish_to_english_months.keys())
                val.sort(key=len)
                val.reverse()
                for i in val:
                    if i in str(date):
                        date = date.replace(i, swedish_to_english_months[i])
                        date = datetime.strptime(date, '%d%B%Y')
                        break
        except ValueError:
            return False

        try:
            if date > datetime.now() or date.year < 2018:
                if not ignore_file:
                    return get_date_from_text(text[text.index(temp) + len(temp):],
                                              ignore_file=True, first_date=date.date())

                return get_date_from_text(text[text.index(temp) + len(temp):],
                                          ignore_file=ignore_file, first_date=first_date)

            return date.date()
        except Exception as e:
            print(date, f'>>> {e}')
    if ignore_file:
        return first_date
    return False


def get_organ_from_text(text):  # last
    if "protokoll" not in text:
        return False
    if Organ.S.label in text and Organ.F.label in text:
        return Organ.S.value if text.index(Organ.S.label) < text.index(Organ.F.label) else Organ.F.value
    elif Organ.S.label in text:
        return Organ.S.value
    elif Organ.F.label in text:
        return Organ.F.value
    return False


def is_ignore_file(text, ignore_texts):
    for obj in ignore_texts:
        if obj.text in text:
            return True

    for word in exact_words:
        if word not in text:
            return True
    return False
