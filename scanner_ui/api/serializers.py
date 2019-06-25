from rest_framework import serializers

class DomainsSerializer(serializers.Serializer):
	domain = serializers.CharField(max_length=200)
	scans = serializers.ListField(child=serializers.CharField(max_length=200))
