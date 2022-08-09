from rest_framework import serializers
from .models import Image, Tag, ImageTagLinkage

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 
                  'image_name', 
                  'image_type', 
                  'image_size', 
                  'image_width', 
                  'image_height', 
                  'image_url',
                  'image_hash',
                  'image_thumbnail',
                  'create_by',
                  'creation_datetime']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 
                  'tag_name', 
                  'tag_category', 
                  'create_by',
                  'creation_datetime']


class ImageTagLinkageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageTagLinkage
        fields = ['id', 
                  'image_name', 
                  'tag_name', 
                  'create_by',
                  'creation_datetime']
