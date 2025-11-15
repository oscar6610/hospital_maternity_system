from rest_framework import serializers
from .models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto


class CatNacionalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatNacionalidad
        fields = '__all__'


class CatPuebloOriginarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatPuebloOriginario
        fields = '__all__'


class CatComplicacionPartoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatComplicacionParto
        fields = '__all__'


class CatRobsonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatRobson
        fields = '__all__'


class CatTipoPartoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatTipoParto
        fields = '__all__'