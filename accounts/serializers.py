from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'university', 'state']
        read_only_fields = ['id', 'username']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Customer
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'phone', 'university']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Customer(**validated_data)
        user.set_password(password)
        user.save()
        return user
