import re
from rest_framework import serializers

from .enums import s, f, InformRegion, InformCountry


class FileDetailDocumentSerializer(serializers.Serializer):
    about_text = serializers.SerializerMethodField()
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
        if obj.organ == 's':
            return s
        return f

    def get_about_text(self, obj):
        if self.context['bol']:
            try:
                return '<br>'.join(obj.meta.highlight.text)
            except:
                pass
        return obj.text[300:800]
        # max_len = 400
        # search_query = self.context['request'].query_params.get('search', '').strip()
        # if bool(search_query):
        #     text = ' '.join(str(search_query).split()).lower()
        #
        #     required_pattern = r'".{,}"'
        #     required_text = re.search(required_pattern, text)
        #     if bool(required_text):
        #         required_text = required_text.group()
        #         text = required_text[1:required_text.index('"', 1)].strip()  # last
        #
        #     else:
        #         ignore_pattern = r' -.{,} '
        #         ignore_texts = re.findall(ignore_pattern, ' ' + text + ' ')
        #         if bool(ignore_texts):
        #             for i in ignore_texts[0].split():
        #                 text = text.replace(i.strip(), '')
        #
        #     text = text.strip()
        #     index = obj.text.find(text)
        #     if bool(required_text):
        #         p = rf'\W{text}\W'
        #         #search_text = re.search(p, obj.text).group()
        #         #index = obj.text.find(search_text)
        #     if index == -1:
        #         for i in text.split():
        #             index = obj.text.find(i)
        #             if index != -1:
        #                 break
        #         else:
        #             return obj.text[300:800].strip()
        #     old_next_symbol_len = abs(max_len - len(text)) // 2
        #     start = 0 if index - old_next_symbol_len <= 0 else index - old_next_symbol_len
        #     end = index + len(text) + old_next_symbol_len
        #     result = obj.text[start:end]
        #     if len(result) < 400:
        #         result = result + ' ' + result[end:end + 400 - len(result)]
        #     return result.strip()
        # return obj.text[300:800].strip()

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
