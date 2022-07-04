from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ImageSerializer, TagSerializer, ImageTagLinkageSerializer
from .models import Image, Tag, ImageTagLinkage

class ImageView(viewsets.ModelViewSet):
    serializer_class = ImageSerializer
    queryset = Image.objects.all()


class TagView(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def list(self, request, *args, **kwargs):
        """ over ride list function
        """
        # retrieve parameter query
        tag_name = self.request.query_params.get('tag_name')
        tag_category = self.request.query_params.get('tag_category')
        queryset = Tag.objects.all()

        # if tag name is passed
        if tag_name is not None and tag_name != '':
            queryset = queryset.filter(tag_name__contains=tag_name)
    
        # if tag categroy is passed
        if tag_category is not None and tag_category != '':
            queryset = queryset.filter(tag_category__contains=tag_category)

        # pagnation
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            return Response({'message': 'List query failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """ override create function
        """
        # retrieve tag name
        new_tag_name = request.data['tag_name']
        # search by name
        old_tag = Tag.objects.all().filter(tag_name=new_tag_name)
        # if not null means tag name already exist
        if old_tag is not None and len(old_tag) > 0:
            return Response({'message': f'tag name [{new_tag_name}] already exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return super().create(request, *args, **kwargs)

    
    


class ImageTagLinkView(viewsets.ModelViewSet):
    serializer_class = ImageTagLinkageSerializer
    queryset = ImageTagLinkage.objects.all()
