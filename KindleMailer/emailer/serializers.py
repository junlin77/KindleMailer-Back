from rest_framework import serializers

class BookSerializer(serializers.Serializer):
    Author = serializers.CharField()
    Title = serializers.CharField()
    Publisher = serializers.CharField()
    Year = serializers.CharField()
    Pages = serializers.CharField()
    Language = serializers.CharField()
    Size = serializers.CharField()
    Extension = serializers.CharField()

