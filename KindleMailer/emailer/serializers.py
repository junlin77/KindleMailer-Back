from rest_framework import serializers

class BookSerializer(serializers.Serializer):
    title = serializers.CharField()
    author = serializers.CharField()
    publisher = serializers.CharField(required=False, allow_blank=True)
    isbn = serializers.CharField(allow_null=True, required=False)
    extension = serializers.CharField()
    filesize = serializers.IntegerField()
    year = serializers.CharField(required=False, allow_blank=True)
    id = serializers.IntegerField()
    source = serializers.CharField()

class DetailsSerializer(serializers.Serializer):
    title = serializers.CharField()
    author = serializers.CharField()
    isbn = serializers.CharField(allow_null=True, required=False)
    extension = serializers.CharField()
    filesize = serializers.IntegerField()
    pages = serializers.IntegerField()
    md5 = serializers.CharField()
    ipfs_cid = serializers.CharField()
    id = serializers.IntegerField()
    source = serializers.CharField()