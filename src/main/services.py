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

    ocrmypdf.ocr(input_file=input_file,
                 output_file=input_file,
                 deskew=True,
                 pdfa_image_compression='jpeg',
                 output_type='pdfa',
                 skip_big=50,
                 language='swe',
                 force_ocr=True)
#    ocrmypdf.ocr(
#        input_file, input_file, output_type='pdf',
#        rotate_pages=True, deskew=True, language='swe', force_ocr=True, max_image_mpixels=30000000
#    )


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


def get_date_from_text(text, ignore_file=False, first_date=None):
    date_pattern = r'(\d{4} ?(-|‐) ?(0[1-9]|1[012]) ?(-|‐) ?(0[1-9]|[12][0-9]|3[01]))|((0[1-9]|[12][0-9]|3[01]) ?. ?(0[1-9]|1[012]) ?. ?\d{4})|((0?[1-9]|[12][0-9]|3[01]) ?(Januari|januari|Jan|jan|Februari|februari|Feb|feb|Mars|mars|Mar|mar|April|april|Apr|apr|Maj|maj|Juni|juni|Jun|jun|Juli|juli|Jul|jul|Augusti|augusti|Aug|aug|September|september|Sep|sep|Oktober|oktober|Okt|okt|November|november|Nov|nov|December|december|Dec|dec) ?\d{4})'
    date = re.search(date_pattern, text)
    if bool(date):
        temp = date.group()
        date = ''.join([i for i in ''.join(date.group().split()) if i.isalpha() or i.isdigit() or i == '.']).strip()
        if bool(date):
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
        else:
            return False
        try:
            if date > datetime.now():
                return get_date_from_text(text[text.find(temp) + len(temp):], 
                                          ignore_file=ignore_file, 
                                          first_date=first_date)
            if date < datetime(year=2018, month=1, day=1):
                if not ignore_file:
                    return get_date_from_text(text[text.find(temp) + len(temp):],
                                              ignore_file=True,
                                              first_date=date.date())
                return get_date_from_text(text[text.find(temp) + len(temp):],
                                          ignore_file=ignore_file,
                                          first_date=first_date)
            return date.date()
        except Exception as e:
            print(date, f'>>> {e}')
    if ignore_file:
        return first_date
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

