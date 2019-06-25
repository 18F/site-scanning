from rest_framework import serializers

class DomainsSerializer(serializers.Serializer):
	domain = serializers.CharField(max_length=200)
	scans = serializers.ListField(child=serializers.CharField(max_length=200))

class ScansSerializer(serializers.Serializer):
	scan = serializers.CharField(max_length=200)
	domains = serializers.ListField(child=serializers.CharField(max_length=200))
