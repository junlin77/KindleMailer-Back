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
    Mirror_1 = serializers.CharField()
    Mirror_2 = serializers.CharField()
    Mirror_3 = serializers.CharField()
    Mirror_4 = serializers.CharField(required=False)
    Mirror_5 = serializers.CharField(required=False)


