import os
import re
import sys
import time
import urllib
import urllib3
import requests
import openpyxl
import threading
from uuid import uuid4
from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.db.utils import DataError
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin, urlparse, urlunparse

from . import models, enums
from .enums import s, f
from . import services

token = '[-!#-\'*+.\dA-Z^-z|~]+'
qdtext = '[]-~\t !#-[]'
mimeCharset = '[-!#-&+\dA-Z^-z]+'
language = '(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}(?:-[A-Za-z]{3}){,2})?|[A-Za-z]{4,8})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|\d{3}))(?:-(?:[\dA-Za-z]{5,8}|\d[\dA-Za-z]{3}))*(?:-[\dA-WY-Za-wy-z](?:-[\dA-Za-z]{2,8})+)*(?:-[Xx](?:-[\dA-Za-z]{1,8})+)?|[Xx](?:-[\dA-Za-z]{1,8})+|[Ee][Nn]-[Gg][Bb]-[Oo][Ee][Dd]|[Ii]-[Aa][Mm][Ii]|[Ii]-[Bb][Nn][Nn]|[Ii]-[Dd][Ee][Ff][Aa][Uu][Ll][Tt]|[Ii]-[Ee][Nn][Oo][Cc][Hh][Ii][Aa][Nn]|[Ii]-[Hh][Aa][Kk]|[Ii]-[Kk][Ll][Ii][Nn][Gg][Oo][Nn]|[Ii]-[Ll][Uu][Xx]|[Ii]-[Mm][Ii][Nn][Gg][Oo]|[Ii]-[Nn][Aa][Vv][Aa][Jj][Oo]|[Ii]-[Pp][Ww][Nn]|[Ii]-[Tt][Aa][Oo]|[Ii]-[Tt][Aa][Yy]|[Ii]-[Tt][Ss][Uu]|[Ss][Gg][Nn]-[Bb][Ee]-[Ff][Rr]|[Ss][Gg][Nn]-[Bb][Ee]-[Nn][Ll]|[Ss][Gg][Nn]-[Cc][Hh]-[Dd][Ee]'
valueChars = '(?:%[\dA-F][\dA-F]|[-!#$&+.\dA-Z^-z|~])*'
dispositionParm = f'[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\s*=\s*(?:({token})|"((?:{qdtext}|\\\\[\t !-~])*)")|[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\*\s*=\s*({mimeCharset})\'(?:{language})?\'({valueChars})|{token}\s*=\s*(?:{token}|"(?:{qdtext}|\\\\[\t !-~])*")|{token}\*\s*=\s*{mimeCharset}\'(?:{language})?\'{valueChars}'

headers_html = {
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.54",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    'referer': 'https://www.google.com/'
}


@shared_task
def detect_pdfs(directory_path, zip_file_model_id):
    print('detect_pdfs ------------------------------------------- start')
    zip_file_model = models.ZipFileUpload.objects.get(id=zip_file_model_id)

    cnt = 0
    objs = []

    regions = os.listdir(directory_path)
    for region in regions:
        normalizing_region = ' '.join(region.split()).strip().lower()
        try:
            model_region = enums.InformRegion.choices()[
                enums.InformRegion.values().index(normalizing_region)
            ][0]
        except ValueError:
            continue

        organs_path = os.path.join(directory_path, region)
        organs = os.listdir(organs_path)
        for organ in organs:
            normalizing_organ = ' '.join(organ.split()).strip().lower()
            if normalizing_organ == 'kf':
                model_organ = 'f'
            elif normalizing_organ == 'ks':
                model_organ = 's'
            else:
                break

            years_path = os.path.join(organs_path, organ)
            try:
                years = os.listdir(years_path)
            except:
                continue
            for year in years:
                try:
                    pdf_files = os.listdir(os.path.join(years_path, year))
                    for pdf_file in pdf_files:
                        location = f'{directory_path}/{region}/{organ}/{year}/{pdf_file}'
                        pdf_file = "".join(pdf_file.split())
                        file_format = pdf_file.split('.')[-1].lower()
                        normalize_location = f'{directory_path}/{region}/{organ}/{year}/{pdf_file}'
                        os.rename(location, normalize_location)
                        if file_format == 'doc' or file_format == 'docx':
                            services.convert_word_to_pdf(normalize_location,
                                                         f'{directory_path}/{region}/{organ}/{year}')
                            file_format = file_format.replace('docx', 'pdf').replace('doc', 'pdf')
                            pdf_file = '.'.join(pdf_file.split('.')[:-1]) + f'.{file_format}'

                        obj = models.FileDetail.objects.create(
                            country=model_region[:3],
                            region=model_region,
                            organ=model_organ,
                            zip_file_id=zip_file_model_id,
                            logo_id=models.Logo.objects.get(region=model_region).id,
                            file=f'zip_files/{directory_path.split("/")[-1]}/{region}/{organ}/{year}/{pdf_file}'
                        )
                        cnt += 1
                        extract_local_pdf(obj.id, obj.file.path)
                except:
                    continue

    zip_file_model.pdfs_count = cnt
    zip_file_model.is_completed = True
    zip_file_model.save()
    os.remove(zip_file_model.zip_file.path)
    print('detect_pdfs ------------------------------------------- end')


@shared_task
def extract_local_pdf(obj_id, pdf_file):
    print('extract_local_pdf ------------------------------------------- start')
    obj = models.FileDetail.objects.get(id=obj_id)

    try:
        obj.text, obj.pages = services.get_text_and_pages(pdf_file)
        obj.size = round(os.path.getsize(pdf_file) / 1_000_000, 2)

        if not obj.file_date:
            date = services.get_date_from_text(obj.text[:2100])
            obj.file_date = date if bool(date) else None
        filename = f'{uuid4()}.pdf'
        location = f'{obj.country}/{obj.region}/{obj.organ}/{obj.file_date}/{filename}'
        new_path = f'{settings.MEDIA_ROOT}/{location}'
        save_dir = os.path.dirname(new_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        os.rename(pdf_file, new_path)
        obj.file = location
        obj.save()
    except Exception as e:
        print(e)
        obj.pages = 1
        obj.save()
    print('extract_local_pdf ------------------------------------------- end')


def is_desired_date(date):
    return True if date.year >= 2018 else False


@shared_task
def extract_url_pdf(webpage_url, inform_id):
    print('extract ------------------------------------------- start')
    inform = models.Inform.objects.get(id=inform_id)
    inform.is_completed = False
    inform.save()

    try:
        logo_id = models.Logo.objects.filter(region=inform.region)
        if not logo_id.exists():
            logo_id = models.Logo.objects.last().id
        else:
            logo_id = logo_id.first().id
        r = requests.get(webpage_url, headers=headers_html, allow_redirects=True, verify=False, stream=True)
    except Exception as e:
        print('extract ------------------------------------------- bad url')
        inform.is_completed = True
        inform.save()
        print(222222222222)
        return

    ignore_texts_from_filename = models.IgnoreText.objects.filter(from_filename=True).values_list('text', flat=True)
    ignore_texts_from_first_page = models.IgnoreText.objects.filter(from_filename=False).values_list('text', flat=True)
    ignore_files = models.IgnoreFile.objects.filter(
        link=webpage_url
    ).values_list('source_file_link', flat=True)
    available_files = models.FileDetail.objects.values_list('source_file_link', flat=True)

    urllib3.disable_warnings(InsecureRequestWarning)
    lock = threading.Lock()

    threads_running = 0

    def threaded_extract(url, filename, view_file_name, retry=0):
        nonlocal threads_running
        if retry > 3:
            threads_running -= 1
            with lock:
                checked_links[url] = 1
            return

        fname = None
        try:
            r = requests.get(url, headers=headers_html, allow_redirects=True, verify=False, stream=True)

            if r.status_code != 200:
                if r.status_code not in [503, 502, 504]:
                    retry += 1
                    return threaded_extract(url, filename, view_file_name, retry=retry)
                else:
                    with lock:
                        checked_links[url] = 1

                    threads_running -= 1
                    return

            if 'pdf' not in r.headers.get('content-type', '').lower():
                threads_running -= 1
                with lock:
                    checked_links[url] = 1
                return

            if r.headers.get('content-disposition'):
                m = re.match(f'(?:{token}\s*;\s*)?(?:{dispositionParm})(?:\s*;\s*(?:{dispositionParm}))*|{token}',
                             r.headers.get('content-disposition'))
                if m:
                    if m.group(8) is not None:
                        fname = urllib.unquote(m.group(8)).decode(m.group(7))

                    elif m.group(4) is not None:
                        fname = urllib.unquote(m.group(4)).decode(m.group(3))

                    elif m.group(6) is not None:
                        fname = re.sub('\\\\(.)', '\1', m.group(6))

                    elif m.group(5) is not None:
                        fname = m.group(5)

                    elif m.group(2) is not None:
                        fname = re.sub('\\\\(.)', '\1', m.group(2))
                    else:
                        fname = m.group(1)
                    if fname:
                        fname = os.path.basename(fname)

            if not fname:
                fname = filename
            if not fname:
                fname = "Document"

            fname = re.sub('[\\/:*?"<>|]', '', fname)

            with lock:
                if not dup_names.get((fname + '.pdf').lower()):
                    dup_names[fname + '.pdf'.lower()] = 1
                    fname = fname + '.pdf'
                else:
                    name_c = 1
                    while True:
                        fname = fname + f'-{name_c}.pdf'
                        if not dup_names.get(fname.lower()):
                            dup_names[fname.lower()] = 1
                            break
                        name_c += 1

            pdf_links[url] = fname
            pdf_view_file_names.append(view_file_name)
            print(url)

        except Exception as e:
            if 'Exceeded' in str(e) and 'redirects' in str(e):
                threads_running -= 1
                with lock:
                    checked_links[url] = 1
                return
            retry += 1
            return threaded_extract(url=url, filename=filename, view_file_name=view_file_name, retry=retry)
        threads_running -= 1

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    os.chdir(application_path)

    pdf_links = {}
    pdf_view_file_names = []
    dup_names = {}
    checked_links = {}

    objs = []
    current_url = r.url
    page_source = r.content

    soup = BeautifulSoup(page_source, 'lxml')

    print('\nChecking links for pdf...')
    for a in soup.findAll('a'):
        link = urljoin(current_url, a.get('href'))
        link = list(urlparse(link))
        link[5] = ""
        link = urlunparse(link)
        filename = link.split('/')[-1]
        view_file_name = ' '.join(str(a.text).lower().split()).strip()
        if pdf_links.get(link):
            continue
        if checked_links.get(link):
            continue

        if link in ignore_files:
            print(f'{link}      - --------------------------ignore file')
            continue
        elif link in available_files:
            print(f'{link}      - --------------------------available file')
            continue
        elif [text for text in ignore_texts_from_filename if text in view_file_name + str(link).lower()]:
            print(f'{link}      - --------------------------ignore text')
            continue

        kwargs = {'url': link, 'filename': filename, 'view_file_name': view_file_name}
        threading.Thread(target=threaded_extract, kwargs=kwargs).start()
        threads_running += 1

    while threads_running > 6:
        time.sleep(.3)

    print(f'\nFound "{len(pdf_links)}" pdf links.')
    print('\nDownloading pdfs...\n')
    pdf_links_copy = pdf_links.copy()
    for index, (pdf_link, pdf_name) in enumerate(pdf_links_copy.items(), 0):
        view_file_name = pdf_view_file_names[index]

        date = services.get_date_from_text(view_file_name + str(pdf_name))
        if date and not is_desired_date(date):
            print(f'{pdf_link}---------------------------------ignore date')
            continue
        print(pdf_link)
        pdf_name = f'{uuid4()}.pdf'
        get_organ = False
        if not inform.organ:
            source = view_file_name + str(pdf_link)
            if s in source:
                get_organ = 's'
            elif f in source:
                get_organ = 'f'
        else:
            get_organ = inform.organ if inform.organ in 'sf' else False

        if get_organ and bool(date):
            location = f'{inform.country}/{inform.region}/{get_organ}/{date}/'
            save_path = os.path.join(f'{settings.MEDIA_ROOT}/{location}', pdf_name)  # last
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(save_path, 'wb') as file:
                file.write(requests.get(
                    pdf_link, headers=headers_html, allow_redirects=True, verify=False, stream=True
                ).content)
            try:
                text_in_file, pages = services.get_text_and_pages(save_path)
            except Exception as e:
                os.remove(save_path)
                print(e)
                continue
            if services.is_ignore_file(text_in_file[:500], ignore_texts_from_first_page):
                print(f'{pdf_link}---------------------------------ignore first page')
                os.remove(save_path)
                continue

            objs.append(models.FileDetail(
                text=text_in_file,
                pages=pages,
                size=round(os.path.getsize(save_path) / 1_000_000, 2),
                country=inform.country,
                region=inform.region,
                organ=get_organ,
                file_date=date,
                file=location + pdf_name,
                source_file_link=pdf_link,
                inform_id=inform_id,
                logo_id=logo_id
            ))
        else:
            location = f'{settings.MEDIA_ROOT}/{inform.country}/{inform.region}/test/'
            save_path = os.path.join(location, pdf_name)
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(save_path, 'wb') as file:
                file.write(requests.get(
                    pdf_link, headers=headers_html, allow_redirects=True, verify=False, stream=True
                ).content)

            try:
                text_in_file, pages = services.get_text_and_pages(save_path)
                organ, gr_date = (
                    services.get_organ_from_text(text_in_file[:500]) if not bool(get_organ) else get_organ,
                    services.get_date_from_text(text_in_file[:2100]) if not bool(date) else date
                )
            except Exception as e:
                os.remove(save_path)
                print(e)
                continue
            if not bool(organ):  # last
                continue
            if services.is_ignore_file(text_in_file[:500], ignore_texts_from_first_page):
                os.remove(save_path)
                print(f'{pdf_link}                  -------------------ignore first page')
                continue

            if gr_date and not is_desired_date(gr_date):
                if os.path.isfile(save_path):
                    os.remove(save_path)
                print(f'{pdf_link}                 -------------------------ignore by date')
                continue
            file_date = date or gr_date if bool(date or gr_date) else None
            location = f'{inform.country}/{inform.region}/{organ}/{file_date}/'
            new_save_path = os.path.join(f'{settings.MEDIA_ROOT}/{location}', pdf_name)
            save_dir = os.path.dirname(new_save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            os.rename(save_path, new_save_path)
            objs.append(models.FileDetail(
                text=text_in_file,
                pages=pages,
                size=round(os.path.getsize(new_save_path) / 1_000_000, 2),
                country=inform.country,
                region=inform.region,
                organ=organ,
                file_date=file_date,
                file=location + pdf_name,
                source_file_link=pdf_link,
                inform_id=inform_id,
                logo_id=logo_id,
            ))

        if len(objs) >= 30:
            models.FileDetail.objects.bulk_create(objs)
            for i in inform.filedetail_set.order_by('-id')[:len(objs)]:
                i.save()
            objs = []
    models.FileDetail.objects.bulk_create(objs)
    for i in inform.filedetail_set.order_by('-id')[:len(objs)]:
        dct = {
            'file': i.file, 'logo': i.logo, 'id': i.id, 'pages': i.pages, 'size': i.size, 'country': i.country,
            'region': i.region, 'organ': i.organ, 'file_date': i.file_date, 'text': i.text
        }
        i.save()
    inform.is_completed = True
    inform.save()
    print('extract ------------------------------------------- end')


@shared_task
def loop_links():
    print('loop link ------------------------------------------- start')
    informs = models.Inform.objects.values_list('link', 'id').order_by('-id')
    for link, inform_id in informs:
        print(f'{inform_id}::: {link}')
        extract_url_pdf(link, inform_id)
    print('loop link ------------------------------------------- end')


@shared_task
def create_search_detail_obj(search_text, files_cnt, forwarded, real, remote):
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    elif real:
        ip = real
    else:
        ip = remote

    print('create_search_detail_obj ------------------------------------------- start')
    text = ' '.join(str(search_text).strip().lower().split())
    try:
        models.SearchDetail.objects.get_or_create(text=text, ipaddress=ip, result_files_cnt=files_cnt)
    except DataError:
        print('create_search_detail_obj ------------------------------------------- bad text')
    print('create_search_detail_obj ------------------------------------------- end')


def from_excel(excel_file):
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active
    for row in ws.rows:
        country = row[0].value
        region = row[1].value
        if country is None or str(country).strip().lower() == 'country':
            continue

        country_index, region_index = (
            enums.InformCountry.values().index(str(country).lower()),
            enums.InformRegion.values().index(str(region).lower())
        )
        valid_country, valid_region = (
            enums.InformCountry.choices()[country_index][0],
            enums.InformRegion.choices()[region_index][0]
        )
        organ = str(row[2].value).strip().lower()
        dct = {
            'link': row[3].value[:-1] if row[3].value[-1] == '/' else row[3].value,
            'country': valid_country,
            'region': valid_region,
            'organ': organ if bool(organ) and (organ == 's' or organ == 'f') else None
        }
        print(dct)
        if models.Inform.objects.filter(link=dct['link']).exists():
            continue
        inform = models.Inform.objects.create(**dct)

        extract_url_pdf(inform.link, inform.id)


def test(webpage_url):
    print('extract ------------------------------------------- start')
    try:
        r = requests.get(webpage_url, headers=headers_html, allow_redirects=True, verify=False, stream=True)
    except:
        print(111111111111111111111)
    ignore_texts_from_filename = models.IgnoreText.objects.filter(from_filename=True).values_list('text', flat=True)
    ignore_texts_from_first_page = models.IgnoreText.objects.filter(from_filename=False).values_list('text', flat=True)
    ignore_files = models.IgnoreFile.objects.filter(
        link=webpage_url
    ).values_list('source_file_link', flat=True)
    available_files = models.FileDetail.objects.filter(
        inform__link=webpage_url
    ).values_list('source_file_link', flat=True)

    urllib3.disable_warnings(InsecureRequestWarning)
    lock = threading.Lock()

    threads_running = 0

    def threaded_extract(url, filename, view_file_name, retry=0):
        nonlocal threads_running
        if retry > 3:
            threads_running -= 1
            with lock:
                checked_links[url] = 1
            return

        fname = None
        try:
            r = requests.get(url, headers=headers_html, allow_redirects=True, verify=False, stream=True)

            if r.status_code != 200:
                if r.status_code not in [503, 502, 504]:
                    retry += 1
                    return threaded_extract(url, filename, view_file_name, retry=retry)
                else:
                    with lock:
                        checked_links[url] = 1

                    threads_running -= 1
                    return

            if 'pdf' not in r.headers.get('content-type', '').lower():
                threads_running -= 1
                with lock:
                    checked_links[url] = 1
                return

            if r.headers.get('content-disposition'):
                m = re.match(f'(?:{token}\s*;\s*)?(?:{dispositionParm})(?:\s*;\s*(?:{dispositionParm}))*|{token}',
                             r.headers.get('content-disposition'))
                if m:
                    if m.group(8) is not None:
                        fname = urllib.unquote(m.group(8)).decode(m.group(7))

                    elif m.group(4) is not None:
                        fname = urllib.unquote(m.group(4)).decode(m.group(3))

                    elif m.group(6) is not None:
                        fname = re.sub('\\\\(.)', '\1', m.group(6))

                    elif m.group(5) is not None:
                        fname = m.group(5)

                    elif m.group(2) is not None:
                        fname = re.sub('\\\\(.)', '\1', m.group(2))
                    else:
                        fname = m.group(1)
                    if fname:
                        fname = os.path.basename(fname)

            if not fname:
                fname = filename
            if not fname:
                fname = "Document"

            fname = re.sub('[\\/:*?"<>|]', '', fname)

            with lock:
                if not dup_names.get((fname + '.pdf').lower()):
                    dup_names[fname + '.pdf'.lower()] = 1
                    fname = fname + '.pdf'
                else:
                    name_c = 1
                    while True:
                        fname = fname + f'-{name_c}.pdf'
                        if not dup_names.get(fname.lower()):
                            dup_names[fname.lower()] = 1
                            break
                        name_c += 1

            pdf_links[url] = fname
            pdf_view_file_names.append(view_file_name)
            print(view_file_name)

        except Exception as e:
            if 'Exceeded' in str(e) and 'redirects' in str(e):
                threads_running -= 1
                with lock:
                    checked_links[url] = 1
                return
            retry += 1
            return threaded_extract(url=url, filename=filename, view_file_name=view_file_name, retry=retry)
        threads_running -= 1

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    os.chdir(application_path)

    pdf_links = {}
    pdf_view_file_names = []
    dup_names = {}
    checked_links = {}
    current_url = r.url
    page_source = r.content

    soup = BeautifulSoup(page_source, 'lxml')

    print('\nChecking links for pdf...')
    for a in soup.findAll('a'):
        link = urljoin(current_url, a.get('href'))
        link = list(urlparse(link))
        link[5] = ""
        link = urlunparse(link)
        filename = link.split('/')[-1]
        view_file_name = ' '.join(str(a.text).lower().split()).strip()

        if pdf_links.get(link):
            continue
        if checked_links.get(link):
            continue

        if link in ignore_files:
            continue
        elif link in available_files:
            continue
        elif [text for text in ignore_texts_from_filename if text in view_file_name + str(link).lower()]:
            continue

        date = services.get_date_from_text(view_file_name + filename)
        if date and not date.year >= 2018:
            continue
        if 'kommunstyrelsen' in view_file_name:
            print(view_file_name)
        kwargs = {'url': link, 'filename': filename, 'view_file_name': view_file_name}
        threading.Thread(target=threaded_extract, kwargs=kwargs).start()
        threads_running += 1

    while threads_running > 6:
        time.sleep(.3)

    print(f'\nFound "{len(pdf_links)}" pdf links.')
    print('\nDownloading pdfs...\n')
    pdf_links_copy = pdf_links.copy()
    for index, (pdf_link, pdf_name) in enumerate(pdf_links_copy.items(), 0):
        print(pdf_link)
    print('extract ------------------------------------------- end')
