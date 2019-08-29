from rest_framework import serializers

class ScanSerializer(serializers.Serializer):
	domain = serializers.CharField(max_length=200)
	scantype = serializers.CharField(max_length=200)
	domaintype = serializers.CharField(max_length=200, required=False)
	agency = serializers.CharField(max_length=200, required=False)
	data = serializers.DictField(required=False)
	scan_data_url = serializers.CharField(max_length=400)
	lastmodified = serializers.DateTimeField()
