from rest_framework import serializers

from .enums import InformRegion, InformCountry, Organ
from .models import FileDetail


class FileDetailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileDetail
        exclude = ("logo", "zip_file", "source_file_link", "inform")


class FileDetailDocumentSerializer(serializers.Serializer):
    about_text = serializers.SerializerMethodField()
    text = serializers.CharField()
    size = serializers.FloatField()
    pages = serializers.IntegerField()
    id = serializers.IntegerField()
    file = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    file_date = serializers.DateTimeField(format='%Y-%m-%d')
    country = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    organ = serializers.SerializerMethodField()

    def get_organ(self, obj):
        try:
            return Organ(obj.organ).label
        except ValueError:
            return "protokoll"

    def get_about_text(self, obj):
        if self.context['bol']:
            try:
                return '<br>'.join(obj.meta.highlight.text)
            except:
                pass
        if obj.first_page_text:
            return obj.first_page_text[:2000]
        return obj.text[300:800]

    def get_country(self, obj):
        return getattr(InformCountry, obj.country).value

    def get_region(self, obj):
        return getattr(InformRegion, obj.region).value

    def get_logo(self, obj):
        if obj.logo.logo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.logo.logo)
        return None

    def get_file(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file)
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        auth = getattr(request, 'auth', None)
        if not auth or not getattr(auth, 'can_see_text', False):
            data.pop('text', None)
        return data


class FileDetailDocumentAuthSerializer(FileDetailDocumentSerializer):
    def get_file(self, obj):
        return None


