from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import FileDetail


@registry.register_document
class FileDetailDocument(Document):
    file = fields.TextField(attr='file.url')

    logo = fields.ObjectField(properties={
        'logo': fields.TextField(attr='logo.url'),
    })
    id = fields.IntegerField()

    class Index:
        name = 'files'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = FileDetail
        fields = [
            'pages',
            'size',
            'country',
            'region',
            'organ',
            'is_active',
            'file_date',
            'text'
        ]
