from rest_framework import serializers

class DomainsSerializer(serializers.Serializer):
	domain = serializers.CharField(max_length=200)
	scantype = serializers.CharField(max_length=200)
	data = serializers.DictField(required=False)
	scan_data_url = serializers.CharField(max_length=400)
	lastmodified = serializers.DateTimeField()
