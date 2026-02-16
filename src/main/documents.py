from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import FileDetail


@registry.register_document
class FileDetailDocument(Document):
    file = fields.TextField(attr='file.url')
    text = fields.TextField(analyzer='text_analyzer')

    logo = fields.ObjectField(properties={
        'logo': fields.TextField(attr='logo.url'),
    })
    id = fields.IntegerField()

    class Index:
        name = 'files'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'char_filter': {
                    'special_chars': {
                        'type': 'mapping',
                        'mappings': [
                            '§ => _sect_',
                            '/ => _slash_',
                            ': => _colon_',
                        ],
                    },
                },
                'analyzer': {
                    'text_analyzer': {
                        'type': 'custom',
                         'char_filter': ['special_chars'],
                        'tokenizer': 'standard',
                        'filter': ['lowercase'],
                    },
                },
            },
        }

    class Django:
        model = FileDetail
        fields = [
            'first_page_text',
            'pages',
            'size',
            'country',
            'region',
            'mode',
            'organ',
            'is_active',
            'file_date',
        ]
