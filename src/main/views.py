import re
import calendar
from datetime import datetime
from collections import OrderedDict
from elasticsearch_dsl import Q
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.throttles import IpRangeThrottle
from accounts.permissions import IsAllowedIP
from .tasks import create_search_detail_obj
from .enums import InformCountry, InformRegion, Organ, FileMode
from .models import FileDetail, Logo
from .documents import FileDetailDocument
from .serializers import FileDetailDocumentSerializer, FileDetailCreateSerializer


class FileDetailCreateAPIView(CreateAPIView):
    serializer_class = FileDetailCreateSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        country = serializer.validated_data['country']
        region = serializer.validated_data['region']
        logo_id = Logo.objects.get(country=country, region=region).id
        serializer.save(logo_id=logo_id)


class FileDetailUpdateAPIView(UpdateAPIView):
    serializer_class = FileDetailCreateSerializer
    permission_classes = (IsAuthenticated,)
    queryset = FileDetail.objects


class FiltersView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = ()

    _filter_item = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'value': openapi.Schema(type=openapi.TYPE_STRING),
            'label': openapi.Schema(type=openapi.TYPE_STRING),
        },
    )
    _region_item = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'value': openapi.Schema(type=openapi.TYPE_STRING),
            'label': openapi.Schema(type=openapi.TYPE_STRING),
            'country': openapi.Schema(type=openapi.TYPE_STRING, description='Parent country code'),
        },
    )

    @swagger_auto_schema(
        operation_id='get_filters',
        operation_summary='Get all available filter options',
        operation_description=(
            'Returns all valid values for the filter parameters used in `/files/`.\n\n'
            'Use this endpoint to populate dropdowns and validate filter values on the client side.\n\n'
            '- **countries** — Swedish counties (län)\n'
            '- **regions** — Municipalities (kommun), each linked to a country\n'
            '- **organs** — Types of municipal organs\n'
            '- **modes** — Document modes (Kommun / Region)'
        ),
        responses={
            200: openapi.Response(
                description='Filter options',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'countries': openapi.Schema(type=openapi.TYPE_ARRAY, items=_filter_item),
                        'regions': openapi.Schema(type=openapi.TYPE_ARRAY, items=_region_item),
                        'organs': openapi.Schema(type=openapi.TYPE_ARRAY, items=_filter_item),
                        'modes': openapi.Schema(type=openapi.TYPE_ARRAY, items=_filter_item),
                    },
                ),
            ),
        },
    )
    def get(self, request):
        countries = [{'value': c.name, 'label': c.value} for c in InformCountry]
        regions = [
            {'value': r.name, 'label': r.value, 'country': r.name[:3]}
            for r in InformRegion
        ]
        organs = [{'value': value, 'label': label} for value, label in Organ.choices]
        modes = [{'value': value, 'label': label} for value, label in FileMode.choices]
        return Response({
            'countries': countries,
            'regions': regions,
            'organs': organs,
            'modes': modes,
        })


class CustomPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        count = self.page.paginator.count
        return count


class SearchFilesView(ListAPIView):
    pagination_class = CustomPageNumberPagination
    document_class = FileDetailDocument
    queryset = FileDetail.objects.all()
    permission_classes = (IsAllowedIP,)
    throttle_classes = (IpRangeThrottle,)
    serializer_class = FileDetailDocumentSerializer

    @staticmethod
    def all_q_expression(query):
        return Q('match_phrase', text={'query': query, 'slop': 10})

    @staticmethod
    def ignore_q_expression(query):
        return ~ Q('match_phrase', text=query)

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

    @swagger_auto_schema(
        operation_id='search_files',
        operation_summary='Search municipal documents',
        operation_description=(
            'Full-text search across Swedish municipal documents (protokoll) stored as PDFs.\n\n'
            '**Search syntax:**\n'
            '- Basic: `budget 2024` — matches documents containing all words\n'
            '- Exact phrase: `"kommunstyrelsen protokoll"` — matches the exact phrase\n'
            '- Exclude: `budget -skola` — excludes documents containing "skola"\n\n'
            '**Sorting:**\n'
            '- When `search` is provided: sorted by relevance (default) or by date with `ordering=-file_date`\n'
            '- When `search` is empty: sorted by date descending\n\n'
            '**Note:** The `text` field in the response is only available for authorized IP ranges.'
        ),
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description=(
                    'Search query. Supports exact phrases in quotes and word exclusion with `-` prefix.\n\n'
                    'Examples: `budget`, `"kommunstyrelsen protokoll"`, `budget -skola`'
                ),
                type=openapi.TYPE_STRING,
                default='',
            ),
            openapi.Parameter(
                'mode', openapi.IN_QUERY,
                description='Document mode: `k` = Kommun (municipality), `r` = Region',
                type=openapi.TYPE_STRING,
                enum=['k', 'r'],
                default='k',
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description='Page number (10 results per page)',
                type=openapi.TYPE_INTEGER,
                default=1,
            ),
            openapi.Parameter(
                'ordering', openapi.IN_QUERY,
                description='Sort order. Use `-file_date` to sort by date. Only applies when `search` is provided (otherwise always sorted by date).',
                type=openapi.TYPE_STRING,
                enum=['-file_date'],
            ),
            openapi.Parameter(
                'country', openapi.IN_QUERY,
                description=(
                    'Filter by county (län) code.\n\n'
                    'Examples: `sto` (Stockholm), `ska` (Skåne), `vag` (Västra Götaland)\n\n'
                    'See `GET /filters/` for all valid values.'
                ),
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'region', openapi.IN_QUERY,
                description=(
                    'Filter by municipality (kommun) code.\n\n'
                    'Examples: `sto_sto` (Stockholm), `ska_mal` (Malmö), `vag_got` (Göteborg)\n\n'
                    'See `GET /filters/` for all valid values.'
                ),
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'organ', openapi.IN_QUERY,
                description=(
                    'Filter by organ type.\n\n'
                    'Examples: `s` (Kommunstyrelsen), `f` (Kommunfullmäktige), `rs` (Regionstyrelsen)\n\n'
                    'See `GET /filters/` for all valid values.'
                ),
                type=openapi.TYPE_STRING,
                enum=[choice[0] for choice in Organ.choices],
            ),
            openapi.Parameter(
                'file_date', openapi.IN_QUERY,
                description='Filter by year (4-digit). Example: `2024`',
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: openapi.Response(
                description='Search results',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Total number of matching documents',
                        ),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description='Array of document objects (max 10 per page)',
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Document ID'),
                                    'about_text': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Highlighted search snippet (HTML with <mark> tags) or first page preview',
                                    ),
                                    'text': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Full document text (only for authorized IP ranges with can_see_text=true)',
                                    ),
                                    'size': openapi.Schema(type=openapi.TYPE_NUMBER, description='File size in MB'),
                                    'pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of pages'),
                                    'file': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format='uri',
                                        description='URL to download the PDF file',
                                    ),
                                    'logo': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format='uri',
                                        description='URL of the municipality logo',
                                    ),
                                    'file_date': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format='date',
                                        description='Document date (YYYY-MM-DD)',
                                    ),
                                    'country': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='County name (e.g. Stockholm, Skåne)',
                                    ),
                                    'region': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Municipality name (e.g. Malmö, Uppsala)',
                                    ),
                                    'organ': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Organ name (e.g. kommunstyrelsen, kommunfullmäktige)',
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            ),
            400: openapi.Response(description='Invalid filter parameter (mode, organ, region, country, or file_date)'),
            429: openapi.Response(description='Rate limit exceeded. Retry after the time specified in the Retry-After header.'),
        },
    )
    def get(self, request, *args, **kwargs):
        mode = str(request.query_params.get('mode', FileMode.KOMMUN)).strip()
        page = str(request.query_params.get('page', 1)).strip()
        search_query = str(request.query_params.get('search', '')).strip()
        ordering_query = str(request.query_params.get('ordering', '')).strip()
        filter_organ_query = str(request.query_params.get('organ', '')).strip()
        filter_region_query = str(request.query_params.get('region', '')).strip()
        filter_date_query = str(request.query_params.get('file_date', '')).strip()
        filter_country_query = str(request.query_params.get('country', '')).strip()

        search = self.document_class.search()


        if mode not in FileMode:
            raise ValidationError({'mode': 'is invalid'})
        else:
            search = search.query(self.filter_q_expression({'mode': mode}))
            if mode == FileMode.REGION:
                filter_region_query = None

        if bool(filter_date_query):
            if filter_date_query.isdigit() and len(filter_date_query) == 4:
                search = search.query(self.date_q_expression(int(filter_date_query)))
            else:
                raise ValidationError({'file_date': 'not found'})

        if filter_organ_query:
            if filter_organ_query not in Organ:
                raise ValidationError({'organ': 'not found'})
            else:
                search = search.query(self.filter_q_expression({'organ': filter_organ_query}))

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

            # required text expression
            required_pattern = r'".*?"'
            required_text_list = re.findall(required_pattern, search_query)
            if required_text_list:
                for required_text in required_text_list:
                    search = search.query(self.exact_q_expression(required_text.replace('"', '')))
                    search_query = search_query.replace(required_text, '')
            # ----------------

            # all expression
            a_search_query = search_query.strip().split()
            if a_search_query:
                if len(a_search_query) > 1:
                    search = search.query(self.all_q_expression(' '.join(a_search_query[:-1])))
                search = search.query(Q('match_phrase_prefix', text=a_search_query[-1]))
            # -------------

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
