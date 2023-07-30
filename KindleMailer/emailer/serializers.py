from rest_framework import serializers

class BookSerializer(serializers.Serializer):
    Title = serializers.CharField()
    Author = serializers.CharField()
    Extension = serializers.CharField()
    # Add any other fields you want to include in the API response
