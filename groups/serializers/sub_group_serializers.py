
from groups.model.group import sub_group
from rest_framework import serializers


class SubGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = sub_group
        fields = '__all__'  