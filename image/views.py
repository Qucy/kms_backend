import io
import os
import base64
from PIL import Image as PILImage

from django.http import Http404, FileResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from .serializers import ImageSerializer, TagSerializer, ImageTagLinkageSerializer
from .models import Image, Tag, ImageTagLinkage


class ImageView(viewsets.ModelViewSet):
    """View for image module"""

    serializer_class = ImageSerializer
    queryset = Image.objects.all()

    def list(self, request, *args, **kwargs):
        """
        over ride list function
        """
        # retrieve parameter query

        image_name = self.request.query_params.get("image_name")
        image_type = self.request.query_params.get("image_type")
        create_by = self.request.query_params.get("create_by")

        queryset = Image.objects.all()

        # if tag name is passed
        if image_name is not None and image_name != "":
            queryset = queryset.filter(image_name__contains=image_name)

        # if tag categroy is passed
        if image_type is not None and image_type != "":
            queryset = queryset.filter(image_type__contains=image_type)

        # if tag categroy is passed
        if create_by is not None and create_by != "":
            queryset = queryset.filter(create_by__contains=create_by)

        # pagnation
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        # Converting the image path into images
        for record in serializer.data:
            image_path = record["image_url"]
            img = PILImage.open(image_path)
            buf = io.BytesIO()
            if record['image_type'].lower() in ('jpg', 'jpeg'):
                img.save(buf, format='JPEG')
            elif record['image_type'].lower() == 'png':
                img.save(buf, format='PNG')
            else:
                print(f'Unsupport type {image_type}')
                
            byte_im = base64.b64encode(buf.getvalue())
            record["img"] = byte_im

        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):

        # Extract image payload
        image = request.data["file"]
        image_name = request.data["image_name"]
        create_by = request.data["create_by"]

        # Process the image
        image_file_io = io.BytesIO(image.file.read())
        image_file = PILImage.open(image_file_io)

        # Saving image to the static file
        image_path = "static/" + str(image)
        image_file.save(image_path)
        image_size = str(os.path.getsize(image_path) / 1024) + " KB"

        # Saving the image meta data
        image_width, image_height = image_file.size
        image_type = str(image).split(".")[1]

        # Check whether there are same image_name in database
        existing_image = Image.objects.all().filter(image_name=image_name)
        if existing_image is not None and len(existing_image) > 0:
            return Response(
                {"message": f"Image name [{image_name}] already exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            Image(
                image_name=image_name,
                image_type=image_type,
                image_size=image_size,
                image_width=image_width,
                image_height=image_height,
                image_url=image_path,
                image_desc=image_path,
                create_by=create_by,
            ).save()
            return Response(
                {"message": f"Image name [{image_name}] created"},
                status=status.HTTP_200_OK,
            )

    @action(detail=False, methods=["get"], name="Download image")
    def download(self, request, *args, **kwargs):
        """ Given the image url download image from local server
            by assign Cotent-Disposition to http header
            https://github.com/eligrey/FileSaver.js/wiki/Saving-a-remote-file#using-http-header
        """
        # retrieve image url
        image_url = self.request.query_params.get("image_url")
        image_name = self.request.query_params.get("image_namme")

        if image_url is not None and image_url != '':

            if os.path.isfile(image_url):
                # open the file
                f = open(image_url, 'rb')
                # file size in bytes
                size = os.path.getsize(image_url)
                # retrieve image name from path
                if image_name is None or image_name == '':
                    image_name = image_url.split('/')[-1]
                # send file
                response = FileResponse(f, content_type='application/octet-stream; charset=utf-8')
                response['Content-Length'] = size
                response['Content-Disposition'] = f'attachment; filename="{image_name}"; filename*="{image_name}"'
                return response
            else:
                return Response(
                {"message": f"Image {image_url} is not exist!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"message": f"Parameter image_url can not be empty!"},
                status=status.HTTP_400_BAD_REQUEST,
            )



class TagView(viewsets.ModelViewSet):
    """View for image tag module"""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def list(self, request, *args, **kwargs):
        """override list function"""
        # retrieve parameter query
        tag_name = self.request.query_params.get("tag_name")
        tag_category = self.request.query_params.get("tag_category")
        queryset = Tag.objects.all()

        # if tag name is passed
        if tag_name is not None and tag_name != "":
            queryset = queryset.filter(tag_name__contains=tag_name)

        # if tag categroy is passed
        if tag_category is not None and tag_category != "":
            queryset = queryset.filter(tag_category__contains=tag_category)

        # pagnation
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """override create function"""
        # retrieve tag name
        new_tag_name = request.data["tag_name"]
        # search by name
        old_tag = Tag.objects.all().filter(tag_name=new_tag_name)
        # if not null means tag name already exist
        if old_tag is not None and len(old_tag) > 0:
            return Response(
                {"message": f"tag name [{new_tag_name}] already exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """override destroy function"""

        # delete tag
        tag = self.get_object()
        self.perform_destroy(tag)

        # return deleted tag
        serializer = TagSerializer(tag)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], name="All tags")
    def all_tags(self, request, *args, **kwargs):
        queryset = Tag.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageTagLinkView(viewsets.ModelViewSet):
    """View for image tag linkage module"""

    serializer_class = ImageTagLinkageSerializer
    queryset = ImageTagLinkage.objects.all()
