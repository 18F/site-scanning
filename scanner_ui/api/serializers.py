from rest_framework import serializers

class ScansSerializer(serializers.Serializer):
	key = serializers.CharField(max_length=200)
