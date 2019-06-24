from rest_framework import serializers

class ScansSerializer(serializers.ModelSerializer):
	key = serializers.CharField(max_length=200)
	last_modified = serializers.DateTimeField()
