import io
import os
import base64
import ast
import hashlib
import cv2
from PIL import Image as PILImage

from django.http import Http404, FileResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from .serializers import ImageSerializer, TagSerializer, CampaignSerializer,CampaignTagLinkageSerializer
from .models import Image, Tag, Campaign,CampaignTagLinkage

class CampaignTagLinkageView(viewsets.ModelViewSet):
    serializer_class = CampaignTagLinkageSerializer
    queryset = CampaignTagLinkage.objects.all()

    def list(self, request, *args, **kwargs):
        tag_name = self.request.query_params.get("tag_name")
        campaign_id = self.request.query_params.get("campaign_id")
        queryset = CampaignTagLinkage.objects.all()

        # if tag_name is passed
        if tag_name is not None and tag_name != "":
            queryset = queryset.filter(tag_name__contains=tag_name)

        # if tag campaign_id is passed
        if campaign_id is not None and campaign_id != "":
            queryset = queryset.filter(campaign_id__exact=campaign_id)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        tag_names = request.data["tag_names"]
        campaign_id = request.data["campaign_id"]
        creation_datetime = request.data["creation_datetime"]

        for tag_name in tag_names.split(','):
            link = CampaignTagLinkage(
                campaign_id = campaign_id,
                tag_name = tag_name,
                creation_datetime=creation_datetime)
            link.save()

        return Response(
            {"message": f"campaign_id [{campaign_id}] is linked with tag [{tag_names}]"},
            status=status.HTTP_200_OK,
        )

    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        campaign_id = self.request.query_params.get("campaign_id")
        count =  CampaignTagLinkage.objects.all().filter(campaign_id = campaign_id).delete()
        return Response({'message': '{} Links were deleted successfully!'.format(count[0])}, status=status.HTTP_204_NO_CONTENT)


    @action(methods=['patch'], detail=False)
    def patch(self, request, *args, **kwargs):
        tag_name = request.data["tag_name"]
        new_tag_name = request.data["new_tag_name"]

        tag_links = CampaignTagLinkage.objects.filter(tag_name = tag_name).update(tag_name = new_tag_name)
        return Response({'message': f'Updated tag {tag_name} to {new_tag_name}'}, status=status.HTTP_200_OK)


class CampaignView(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = Campaign.objects.all()
        serializer = self.get_serializer(queryset, many=True)

        # Converting the image path into images
        for record in serializer.data:
            image_path = record["campaign_thumbnail_url"]
            img = PILImage.open(image_path)
            buf = io.BytesIO()
            image_type = image_path.split('.')[1]

            if image_type.lower() in ('jpg', 'jpeg'):
                img.save(buf, format='JPEG')
            elif image_type.lower() == 'png':
                img.save(buf, format='PNG')
            else:
                print(f'Unsupport image type ')
                
            byte_im = base64.b64encode(buf.getvalue())
            record["img"] = byte_im

        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageView(viewsets.ModelViewSet):
    """View for image module"""

    serializer_class = ImageSerializer
    queryset = Image.objects.all()

    def list(self, request, *args, **kwargs):
        """
        override list function
        """
        # retrieve parameter query
        image_name = self.request.query_params.get("image_name")
        image_type = self.request.query_params.get("image_type")
        image_names = self.request.query_params.get("image_names")
        campaign_id = self.request.query_params.get("campaign_id")

        queryset = Image.objects.all()

        # if image name is passed
        if image_name is not None and image_name != "":
            queryset = queryset.filter(image_name__contains=image_name)

        # if image type is passed
        if image_type is not None and image_type != "":
            queryset = queryset.filter(image_type__contains=image_type)

        # if image names is passed
        if image_names is not None and image_names != "":
            image_name_list = image_names.split(",")
            queryset = queryset.filter(image_name__in=image_name_list)

        # if creator is passed
        if campaign_id is not None and campaign_id != "":
            queryset = queryset.filter(campaign_id__exact=campaign_id)

        # pagnation
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        # Converting the image path into images TODO remove this code later when all the image have thumbnail
        for record in serializer.data:
            image_path = record["image_thumbnail_url"]
            img = PILImage.open(image_path)
            buf = io.BytesIO()
            if record["image_type"].lower() in ("jpg", "jpeg"):
                img.save(buf, format="JPEG")
            elif record["image_type"].lower() == "png":
                img.save(buf, format="PNG")
            else:
                print(f"Unsupport type {image_type}")

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

        # Saving image to the static file TODO optimized in future, save in tmp folder before below validation is passed
        image_path = "static/" + str(image)
        image_file.save(image_path)
        image_size = str(os.path.getsize(image_path) / 1024) + " KB"

        # Saving the image meta data
        image_width, image_height = image_file.size
        image_type = str(image).split(".")[1]

        # Calc image hash
        image_hash = self._md5(image_path)

        # Check whether there are same image_name in database
        existing_image_name = Image.objects.all().filter(image_name=image_name)

        # Check whether there are same image hash in database
        existing_image_hash = Image.objects.all().filter(image_hash=image_hash)

        if existing_image_name is not None and len(existing_image_name) > 0:
            return Response(
                {"message": f"Image name [{image_name}] already exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif existing_image_hash is not None and len(existing_image_hash) > 0:
            return Response(
                {"message": f"Image [{image_name}] already exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:

            image_thumbnail = self._resize_image(image_type, image_path)

            print(f"image_thumbnail in base64:{image_thumbnail}")

            image = Image(
                image_name=image_name,
                image_type=image_type,
                image_size=image_size,
                image_width=image_width,
                image_height=image_height,
                image_url=image_path,
                image_hash=image_hash,
                image_desc=image_path,
                image_thumbnail=image_thumbnail,
                create_by=create_by,
            )
            image.save()
            return Response(
                {"message": f"Image name [{image_name}] created", "image_id": image.id},
                status=status.HTTP_200_OK,
            )

    @action(detail=False, methods=["get"], name="Download image")
    def download(self, request, *args, **kwargs):
        """Given the image url download image from local server
        by assign Cotent-Disposition to http header
        https://github.com/eligrey/FileSaver.js/wiki/Saving-a-remote-file#using-http-header
        """
        # retrieve image url
        image_url = self.request.query_params.get("image_url")
        image_name = self.request.query_params.get("image_namme")

        if image_url is not None and image_url != "":

            if os.path.isfile(image_url):
                # open the file
                f = open(image_url, "rb")
                # file size in bytes
                size = os.path.getsize(image_url)
                # retrieve image name from path
                if image_name is None or image_name == "":
                    image_name = image_url.split("/")[-1]
                # send file
                response = FileResponse(
                    f, content_type="application/octet-stream; charset=utf-8"
                )
                response["Content-Length"] = size
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{image_name}"; filename*="{image_name}"'
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

    def _md5(self, file_path):
        """calc hash value for image"""
        hash_md5 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _resize_image(self, image_type, image_path):
        """resize image based on previous image size
        and encoded base64 for input image
        """
        # load image
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        # scale down image
        scale_percent = 10  # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        resized_image = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        # get encode type
        encode_type = ".jpg" if image_type.lower() in ["jpg", "jpeg"] else ".png"
        # encode image
        encoded_image = cv2.imencode(encode_type, resized_image)[1]
        # encode image to base64
        encoded_image_base64 = str(base64.b64encode(encoded_image))[2:-1]
        return encoded_image_base64


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

    def update(self, request, pk=None):

        # store and return old_tag_name
        tag = Tag.objects.all().filter(id=pk)
        old_tag_name = ""

        if tag is not None and len(tag) > 0:
            old_tag_name = tag[0].tag_name

        # update the tag object

        new_tag_name = request.data["tag_name"]
        new_create_by = request.data["create_by"]
        new_tag_category = request.data["tag_category"]

        tag.update(
            tag_name=new_tag_name,
            create_by=new_create_by,
            tag_category=new_tag_category,
        )

        return Response(
            {"original_tag_name": old_tag_name},
            status=status.HTTP_200_OK,
        )

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


# class ImageTagLinkView(viewsets.ModelViewSet):
#     """View for image tag linkage module"""

#     serializer_class = ImageTagLinkageSerializer
#     queryset = ImageTagLinkage.objects.all()

#     def list(self, request, *args, **kwargs):

#         # retrieve parameter query
#         image_names = self.request.query_params.get("image_names")
#         tag_name = self.request.query_params.get("tag_name")

#         queryset = ImageTagLinkage.objects.all()

#         # if image_name categroy is passed
#         if image_names is not None and image_names != "":
#             image_name_list = image_names.split(',')
#             queryset = queryset.filter(image_name__in=image_name_list)

#         # if tag categroy is passed
#         if tag_name is not None and tag_name != "":
#             queryset = queryset.filter(tag_name__exact=tag_name)

#         serializer = self.get_serializer(queryset, many=True)

#         return Response(serializer.data, status=status.HTTP_200_OK)


#     def create(self, request, *args, **kwargs):
#         tag_names = request.data["tag_names"]
#         image_name = request.data["image_name"]
#         create_by = request.data["create_by"]
#         creation_datetime = request.data["creation_datetime"]

#         for tag_name in tag_names:
#             link = ImageTagLinkage(
#                 image_name = image_name,
#                 tag_name = tag_name,
#                 create_by = create_by,
#                 creation_datetime=creation_datetime)
#             link.save()

#         return Response(
#             {"message": f"Image [{image_name}] is linked with tag [{tag_name}]"},
#             status=status.HTTP_200_OK,
#         )

#     @action(methods=['delete'], detail=False)
#     def delete(self, request, *args, **kwargs):
#         image_name = self.request.query_params.get("image_name")
#         count =  ImageTagLinkage.objects.all().filter(image_name = image_name).delete()
#         return Response({'message': '{} Links were deleted successfully!'.format(count[0])}, status=status.HTTP_204_NO_CONTENT)


#     @action(methods=['patch'], detail=False)
#     def patch(self, request, *args, **kwargs):
#         tag_name = request.data["tag_name"]
#         new_tag_name = request.data["new_tag_name"]

#         tag_links = ImageTagLinkage.objects.filter(tag_name = tag_name).update(tag_name = new_tag_name)

#         return Response({'message': f'Updated tag {tag_name} to {new_tag_name}'}, status=status.HTTP_200_OK)
