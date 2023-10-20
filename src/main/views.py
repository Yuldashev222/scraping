import re
import calendar
from datetime import datetime
from collections import OrderedDict
from elasticsearch_dsl import Q
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from .tasks import create_search_detail_obj
from .enums import InformCountry, InformRegion
from .models import FileDetail
from .documents import FileDetailDocument
from .serializers import FileDetailDocumentSerializer, FileDetailDocumentAuthSerializer


class CustomPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        count = self.page.paginator.count
        return count
        search_text = str(self.request.query_params.get('search', '')).strip()
        if bool(search_text):
            create_search_detail_obj.delay(search_text=search_text,
                                           files_cnt=count,
                                           forwarded=self.request.META.get('HTTP_X_FORWARDED_FOR'),
                                           real=self.request.META.get('HTTP_X_REAL_IP'),
                                           remote=self.request.META.get('REMOTE_ADDR'))
        return Response(OrderedDict([
            ('count', count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class SearchFilesView(ListAPIView):
    pagination_class = CustomPageNumberPagination
    document_class = FileDetailDocument
    queryset = FileDetail.objects.all()
    permission_classes = ()

    def get_serializer_class(self):
        # if self.request.user.is_authenticated:
        return FileDetailDocumentSerializer
        # return FileDetailDocumentAuthSerializer

    @staticmethod
    def all_q_expression(query):
        return Q('match_phrase', text={'query': query, 'slop': 10})

    @staticmethod
    def ignore_q_expression(query):
        return ~ Q('wildcard', text='*' + query + '*')

    @staticmethod
    def exact_q_expression(query):
        return Q('match_phrase', text=query)

    @staticmethod
    def filter_q_expression(dct):
        return Q('term', **dct)

    @staticmethod
    def date_q_expression(year):
        last_day_of_month = calendar.monthrange(year, 12)[1]
        start_date = datetime(year=year, month=1, day=1)
        end_date = datetime(year=year, month=12, day=last_day_of_month)
        return Q('range', file_date={'gte': start_date, 'lte': end_date})

    def get(self, request, *args, **kwargs):
        page = str(request.query_params.get('page', 1)).strip()
        search_query = str(request.query_params.get('search', '')).strip()
        ordering_query = str(request.query_params.get('ordering', '')).strip()
        filter_organ_query = str(request.query_params.get('organ', '')).strip()
        filter_region_query = str(request.query_params.get('region', '')).strip()
        filter_date_query = str(request.query_params.get('file_date', '')).strip()
        filter_country_query = str(request.query_params.get('country', '')).strip()

        search = self.document_class.search()

        if bool(filter_date_query):
            if filter_date_query.isdigit() and len(filter_date_query) == 4:
                search = search.query(self.date_q_expression(int(filter_date_query)))
            else:
                raise ValidationError({'file_date': 'not found'})

        if bool(filter_organ_query):
            if len(filter_organ_query) == 1 and filter_organ_query in 'sf':
                search = search.query(self.filter_q_expression({'organ': filter_organ_query}))
            else:
                raise ValidationError({'organ': 'not found'})

        if bool(filter_country_query):
            if filter_country_query in InformCountry.keys():
                search = search.query(self.filter_q_expression({'country': filter_country_query}))
            else:
                raise ValidationError({'country': 'not found'})

        if bool(filter_region_query):
            if filter_region_query in InformRegion.keys():
                search = search.query(self.filter_q_expression({'region': filter_region_query}))
            else:
                raise ValidationError({'region': 'not found'})

        bol = bool(search_query)
        if bol:
            search_query = ' '.join(search_query.split()).lower()
            s_copy = search_query

            # ignore text expression
            for word in search_query.split()[::-1]:
                if word[0] != '-':
                    break
                search = search.query(self.ignore_q_expression(word[1:]))
                search_query = search_query.replace(word, '')
            search_query = search_query.strip()
            # ---------------------

            # all expression
            a_search_query = search_query.replace('"', '').strip().split()
            if len(a_search_query) > 1:
                search = search.query(self.all_q_expression(' '.join(a_search_query[:-1])))
            search = search.query(Q('wildcard', text=a_search_query[-1] + '*'))
            # -------------

            # required text expression
            required_pattern = r'".*?"'
            required_text_list = re.findall(required_pattern, search_query)
            if required_text_list:
                for required_text in required_text_list:
                    search = search.query(self.exact_q_expression(required_text.replace('"', '')))
                    search_query = search_query.replace(required_text, '')
            # ----------------

            search = search.highlight('text', fragment_size=130, pre_tags='<mark>', post_tags='</mark>',
                                      max_analyzed_offset=500000)

            if ordering_query == '-file_date':
                search = search.sort('-file_date')
            else:
                search = search.sort({"_score": {"order": "desc"}})


        else:
            search = search.sort('-file_date')

        search = search.query(self.filter_q_expression({'is_active': True}))
        try:
            response = search[(int(page) - 1) * 10:].execute()
        except Exception as e:
            print(e)
            response = search.execute()

        serializer = self.get_serializer_class()(response, many=True, context={'request': request, 'bol': bol})
        self.paginate_queryset(search)
        count = self.get_paginated_response(search)
        if bol:
            create_search_detail_obj.delay(search_text=s_copy,
                                           files_cnt=count,
                                           forwarded=request.META.get('HTTP_X_FORWARDED_FOR'),
                                           real=request.META.get('HTTP_X_REAL_IP'),
                                           remote=request.META.get('REMOTE_ADDR'))
        return Response(OrderedDict([('count', count), ('results', serializer.data)]))
