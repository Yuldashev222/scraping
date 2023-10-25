import os
import re
import sys
import time
import shutil
import urllib3
import requests
import openpyxl
import threading
from uuid import uuid4
from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.db.utils import DataError
from django.utils.timezone import now
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin, urlparse, urlunparse, unquote

from scraping.models import Scraping, UnnecessaryFile
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

    regions = os.listdir(directory_path)
    for region in regions:
        normalizing_region = ' '.join(region.split()).strip().lower()
        try:
            model_region = enums.InformRegion.choices()[enums.InformRegion.values().index(normalizing_region)][0]
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
                        if file_format in 'docxrtf':
                            services.convert_word_to_pdf(normalize_location,
                                                         f'{directory_path}/{region}/{organ}/{year}')
                            file_format = file_format.replace('docx', 'pdf').replace('doc', 'pdf').replace('rtf', 'pdf')
                            pdf_file = '.'.join(pdf_file.split('.')[:-1]) + f'.{file_format}'

                        obj = models.FileDetail.objects.create(country=model_region[:3],
                                                               region=model_region,
                                                               is_active=True,
                                                               organ=model_organ,
                                                               zip_file_id=zip_file_model_id,
                                                               logo_id=models.Logo.objects.get(region=model_region).id,
                                                               file=f'zip_files/{directory_path.split("/")[-1]}/{region}/{organ}/{year}/{pdf_file}')
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
            date = services.get_date_from_text(obj.text[:4000])
            if date and not services.is_desired_date(date):
                obj.delete()
                return
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
        print(str(e))
        print('extract ------------------------------------------- bad url')
        inform.is_completed = True
        inform.save()
        return

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

            if 'pdf' not in r.headers.get('content-type', '').lower():  # last
                threads_running -= 1
                with lock:
                    checked_links[url] = 1
                return

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
            print(str(e))
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
    try:
        page_source = r.content

        soup = BeautifulSoup(page_source, 'lxml')
    except Exception as e:
        print(str(e))
        print('extract ------------------------------------------- bad chunk')
        inform.is_completed = True
        inform.save()
        return

    print('\nChecking links for pdf...')
    ignore_texts_from_filename = models.IgnoreText.objects.filter(from_filename=True)
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

        if UnnecessaryFile.objects.filter(inform_id=inform.id, pdf_link=link).exists():
            print(f'{link}      ---------------------------unnecessary file')
            continue
        elif models.IgnoreFile.objects.filter(link=webpage_url, source_file_link=link).exists():
            print(f'{link}      ---------------------------ignore file')
            continue
        elif models.FileDetail.objects.filter(source_file_link=link).exists():
            print(f'{link}      ---------------------------available file')
            continue
        else:
            temp_name = view_file_name + str(link).lower()
            ignore_text = False
            for obj in ignore_texts_from_filename:
                if obj.text in temp_name:
                    print(f'{link}      ---------------------------ignore text')
                    ignore_text = True
                    break
            if ignore_text:
                try:
                    r_test = requests.head(link)
                    if dict(r_test.headers).get('Content-Type') == 'application/pdf':
                        UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=link)
                except Exception as e:
                    print(e)
                continue

        kwargs = {'url': link, 'filename': filename, 'view_file_name': view_file_name}
        threading.Thread(target=threaded_extract, kwargs=kwargs).start()
        threads_running += 1

    while threads_running > 6:
        time.sleep(.3)

    len_pdfs = len(pdf_links)
    print(f'\nFound "{len_pdfs}" pdf links.')

    ignore_texts_from_first_page = models.IgnoreText.objects.filter(from_filename=False)
    print('\nDownloading pdfs...\n')
    pdf_links_copy = pdf_links.copy()
    last_pdf = None
    new_pdfs = False
    for index, (pdf_link, pdf_name) in enumerate(pdf_links_copy.items(), 0):
        view_file_name = pdf_view_file_names[index]

        date = services.get_date_from_text(view_file_name + str(pdf_name))
        if date and not services.is_desired_date(date):
            print(f'{pdf_link}---------------------------------ignore date')
            try:
                r_test = requests.head(pdf_link)
                if dict(r_test.headers).get('Content-Type') == 'application/pdf':
                    UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=pdf_link)
            except Exception as e:
                print(e)
            continue

        print(pdf_link)

        pdf_name = f'{uuid4()}.pdf'
        get_organ = inform.organ if str(inform.organ) in 'sf' else False
        if not get_organ:
            source = view_file_name + str(pdf_link)
            if s in source:
                get_organ = 's'
            elif f in source:
                get_organ = 'f'

        if get_organ and bool(date):
            location = f'{inform.country}/{inform.region}/{get_organ}/{date}/'
            save_path = os.path.join(f'{settings.MEDIA_ROOT}/{location}', pdf_name)  # last
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(save_path, 'wb') as file:
                file.write(requests.get(
                    pdf_link, headers=headers_html, allow_redirects=True, verify=False, stream=True).content)

            try:
                first_page_text = services.get_pages_text(save_path)
                if services.is_ignore_file(first_page_text, ignore_texts_from_first_page):
                    print(f'{pdf_link}---------------------------------ignore first page')
                    try:
                        r_test = requests.head(pdf_link)
                        if dict(r_test.headers).get('Content-Type') == 'application/pdf':
                            UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=pdf_link)
                    except Exception as e:
                        print(e)
                    os.remove(save_path)
                    os.remove(save_path + '.first_page.pdf')
                    continue
                os.remove(save_path + '.first_page.pdf')
                text_in_file, pages = services.get_text_and_pages(save_path)

                models.FileDetail.objects.create(text=text_in_file,
                                                 first_page_text=first_page_text,
                                                 pages=pages,
                                                 size=round(os.path.getsize(save_path) / 1_000_000, 2),
                                                 country=inform.country,
                                                 region=inform.region,
                                                 organ=get_organ,
                                                 file_date=date,
                                                 file=location + pdf_name,
                                                 source_file_link=pdf_link,
                                                 inform_id=inform_id,
                                                 logo_id=logo_id)
                last_pdf = now()
                new_pdfs = True
            except Exception as e:
                try:
                    r_test = requests.head(pdf_link)
                    if dict(r_test.headers).get('Content-Type') == 'application/pdf':
                        UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=pdf_link)
                except Exception as e:
                    print(e)

                if os.path.isfile(save_path):
                    os.remove(save_path)
                if os.path.isfile(save_path + '.first_page.pdf'):
                    os.remove(save_path + '.first_page.pdf')
                print(e)
                last_pdf = None
                new_pdfs = False

        else:
            location = f'{settings.MEDIA_ROOT}/{inform.country}/{inform.region}/test/'
            save_path = os.path.join(location, pdf_name)
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(save_path, 'wb') as file:
                file.write(requests.get(
                    pdf_link, headers=headers_html, allow_redirects=True, verify=False, stream=True).content)

            try:
                new_save_path = ''
                first_page_text = services.get_pages_text(save_path)
                if services.is_ignore_file(first_page_text, ignore_texts_from_first_page):
                    print(f'{pdf_link}---------------------------------ignore first page')
                    try:
                        r_test = requests.head(pdf_link)
                        if dict(r_test.headers).get('Content-Type') == 'application/pdf':
                            UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=pdf_link)
                    except Exception as e:
                        print(e)

                    os.remove(save_path)
                    os.remove(save_path + '.first_page.pdf')
                    continue
                os.remove(save_path + '.first_page.pdf')
                text_in_file, pages = services.get_text_and_pages(save_path)
                organ, gr_date = (
                    services.get_organ_from_text(first_page_text) if not bool(get_organ) else get_organ,
                    services.get_date_from_text(first_page_text) if not bool(date) else date
                )
                if gr_date and not services.is_desired_date(gr_date):
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
                models.FileDetail.objects.create(text=text_in_file,
                                                 first_page_text=first_page_text,
                                                 pages=pages,
                                                 size=round(os.path.getsize(new_save_path) / 1_000_000, 2),
                                                 country=inform.country,
                                                 region=inform.region,
                                                 organ=organ,
                                                 file_date=file_date,
                                                 file=location + pdf_name,
                                                 source_file_link=pdf_link,
                                                 inform_id=inform_id,
                                                 logo_id=logo_id)
                last_pdf = now()
                new_pdfs = True
            except Exception as e:
                try:
                    if dict(requests.head(pdf_link).headers).get('Content-Type') == 'application/pdf':
                        UnnecessaryFile.objects.get_or_create(inform_id=inform.id, pdf_link=pdf_link)
                except Exception as e:
                    print(e)

                if os.path.isfile(new_save_path):
                    os.remove(new_save_path)
                if os.path.isfile(save_path):
                    os.remove(save_path)
                if os.path.isfile(save_path + '.first_page.pdf'):
                    os.remove(save_path + '.first_page.pdf')
                print(e)
                last_pdf = None
                new_pdfs = False

    inform.is_completed = True
    inform.new_pdfs = new_pdfs
    if last_pdf is not None:
        inform.last_pdf = last_pdf
    inform.save()
    try:
        shutil.rmtree(f'{settings.MEDIA_ROOT}{inform.country}/{inform.region}/test/')
    except FileNotFoundError:
        pass
    print('extract ------------------------------------------- end')


@shared_task
def loop_links(start_inform_id):
    print('loop link ------------------------------------------- start')
    if start_inform_id == 0:
        max_inform_id = models.Inform.objects.aggregate(mx=models.models.Max('id'))['mx']
        if max_inform_id:
            start_inform_id = max_inform_id
    informs = models.Inform.objects.filter(
        id__lte=start_inform_id).exclude(models.models.Q(id__in=[1058, 856, 855, 854, 853, 852]) |
                                         models.models.Q(region__in=['sto_nyn', 'vag_fal', 'sto_nac', 'sto_tab'])
                                         ).values_list('link', 'id').order_by('-id')
    for link, inform_id in informs:
        obj = Scraping.objects.first()
        if obj and not obj.play:
            print('loop link ------------------------------------------- pause')
            obj.pause_inform_id = inform_id
            obj.save()
            return
        print(f'{inform_id}::: {link}')
        try:
            extract_url_pdf(link, inform_id)
        except Exception as e:
            print(str(e))

    obj = Scraping.objects.first()
    if obj:
        obj.pause_inform_id = 0
        obj.save()
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
