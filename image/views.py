import io
import os
import base64
import ast
import hashlib
import datetime
import cv2
from PIL import Image as PILImage

from django.http import Http404, FileResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from .serializers import (
    ImageSerializer,
    TagSerializer,
    CampaignSerializer,
    CampaignTagLinkageSerializer,
)
from .models import Image, Tag, Campaign, CampaignTagLinkage
from .utils import expand2square

THUMBNAIL_SIZE = 550, 550
CAMPAIGN_THUMBNAIL_PATH = "static/thumbnail/"


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

        # Filter the campaign with campaign id
        if campaign_id is not None and campaign_id != "":
            queryset = queryset.filter(campaign_id__exact=campaign_id)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        tag_names = request.data["tag_names"]
        campaign_id = request.data["campaign_id"]
        creation_datetime = str(datetime.datetime.now())

        for tag_name in tag_names.split(","):
            link = CampaignTagLinkage(
                campaign_id=campaign_id,
                tag_name=tag_name,
                creation_datetime=creation_datetime,
            )
            link.save()

        return Response(
            {
                "message": f"campaign_id [{campaign_id}] is linked with tag [{tag_names}]"
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=["delete"], detail=False)
    def delete(self, request, *args, **kwargs):
        campaign_id = self.request.query_params.get("campaign_id")
        count = (
            CampaignTagLinkage.objects.all().filter(campaign_id=campaign_id).delete()
        )
        return Response(
            {"message": "{} Links were deleted successfully!".format(count[0])},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(methods=["patch"], detail=False)
    def patch(self, request, *args, **kwargs):
        tag_name = request.data["tag_name"]
        new_tag_name = request.data["new_tag_name"]

        tag_links = CampaignTagLinkage.objects.filter(tag_name=tag_name).update(
            tag_name=new_tag_name
        )
        return Response(
            {"message": f"Updated tag {tag_name} to {new_tag_name}"},
            status=status.HTTP_200_OK,
        )


class CampaignView(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = Campaign.objects.all()

        # Extract the request params
        tag_names = self.request.query_params.get("tag_names")
        company = self.request.query_params.get("company")
        hsbc_vs_non_hsbc = self.request.query_params.get("hsbc_vs_non_hsbc")
        location = self.request.query_params.get("location")
        message_type = self.request.query_params.get("message_type")

        # Filtering logic on hsbc_vs_non_hsbc (AND condition)
        if hsbc_vs_non_hsbc:
            queryset = queryset.filter(hsbc_vs_non_hsbc__exact=hsbc_vs_non_hsbc)

        # Filtering logic on company (AND condition)
        if company:
            queryset = queryset.filter(company__exact=company)

        # Filtering logic on message_type (AND condition)
        if message_type:
            queryset = queryset.filter(message_type__exact=message_type)

        # Filtering logic on tags (AND condition)
        if tag_names is not None and tag_names != "":
            # Extract the tags filter
            tags = tag_names.split(",")

            filter_list = []
            for tag in tags:
                # Query the campaign tag linkage to get unique campaign id containing the specific tags
                tag_queryset = CampaignTagLinkage.objects.all()
                tag_queryset = tag_queryset.filter(tag_name__exact=tag)
                campaign_ids = list(
                    set([int(campaign.campaign_id) for campaign in tag_queryset])
                )
                filter_list.append(campaign_ids)

            result_campadign_ids = set(filter_list[0])
            if len(filter_list) > 1:
                for s in filter_list[1:]:
                    result_campadign_ids.intersection_update(s)

            result_campadign_ids = list(result_campadign_ids)
            # Filter campaign by campaign id
            queryset = queryset.filter(pk__in=result_campadign_ids)

        # Serialize data
        serializer = self.get_serializer(queryset, many=True)

        # Converting the image path into images
        for record in serializer.data:
            image_path = record["campaign_thumbnail_url"]
            img = PILImage.open(image_path)
            buf = io.BytesIO()
            image_type = image_path.split(".")[1]

            if image_type.lower() in ("jpg", "jpeg"):
                img.save(buf, format="JPEG")
            elif image_type.lower() == "png":
                img.save(buf, format="PNG")
            else:
                print(f"Unsupport image type ")

            byte_im = base64.b64encode(buf.getvalue())
            record["img"] = byte_im

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        if "tag_names" in request.data:
            tag_names = request.data["tag_names"]
            instance = self.get_object()

            # Delete CampaignTagLinkage for the campaign id
            camapign_taglink_queryset = CampaignTagLinkage.objects.all().filter(
                campaign_id__exact=instance.id
            )
            camapign_taglink_queryset.delete()

            # Generate the new createion_datetime
            creation_datetime = str(datetime.datetime.now())

            # Re-create the campaign linkage for campaign id
            for tag_name in tag_names.split(","):
                link = CampaignTagLinkage(
                    campaign_id=instance.id,
                    tag_name=tag_name,
                    creation_datetime=creation_datetime,
                )
                link.save()

        return super().partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):

        # Extract image payload
        company = request.data["company"]
        hsbc_vs_non_hsbc = request.data["hsbc_vs_non_hsbc"]
        location = request.data["location"]
        response_rate = request.data["response_rate"]
        message_type = request.data["message_type"]
        image = request.data["file"]

        # Calcualte the current datetime
        creation_datetime = str(datetime.datetime.now())

        # Process the image
        image_file_io = io.BytesIO(image.file.read())
        image_file = PILImage.open(image_file_io)
        image_file = expand2square(image_file, "white").resize(THUMBNAIL_SIZE)

        # Saving image to the static file TODO optimized in future, save in tmp folder before below validation is passed
        image_path = CAMPAIGN_THUMBNAIL_PATH + str(image)
        image_file.save(image_path)

        campaign = Campaign(
            company=company,
            hsbc_vs_non_hsbc=hsbc_vs_non_hsbc,
            location=location,
            message_type=message_type,
            response_rate=response_rate,
            campaign_thumbnail_url=image_path,
            creation_datetime=creation_datetime,
        )

        campaign.save()

        return Response(
            {"message": f"Campaign  created", "campaign_id": campaign.id},
            status=status.HTTP_200_OK,
        )

    def perform_destroy(self, instance):
        # Delete the campaign thumbnail file
        campaign_thumbnail_file_path = instance.campaign_thumbnail_url
        os.remove(campaign_thumbnail_file_path)

        # Filter out the images related to the campaign
        image_queryset = Image.objects.all().filter(campaign_id__exact=instance.id)

        # Delete thumbnail image files
        image_file_paths = [image.image_url for image in image_queryset]
        for image_file_path in image_file_paths:
            os.remove(image_file_path)

        # Delete thumbnail image files
        image_thumbnail_file_paths = [
            image.image_thumbnail_url for image in image_queryset
        ]
        for image_thumbnail_file_path in image_thumbnail_file_paths:
            os.remove(image_thumbnail_file_path)

        # Delete image queryset
        image_queryset.delete()

        # Delete CampaignTagLinkage
        camapign_taglink_queryset = CampaignTagLinkage.objects.all().filter(
            campaign_id__exact=instance.id
        )
        camapign_taglink_queryset.delete()

        # Delete Campaign Instance
        instance.delete()

    @action(detail=False, methods=["patch"], name="update campaign status")
    def updateStatus(self, request):
        """api to approve new created campaign"""
        # Extract PK
        campaign_id = request.data["id"]
        campaign_status = request.data["status"]
        # sanity check before update
        if campaign_id is None:
            return Response(
                {"message": f"Campaign id can not be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if campaign_status is None or campaign_status == "":
            return Response(
                {"message": f"Campaign status can not be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif campaign_status not in ["APPROVED", "NEW"]:
            return Response(
                {"message": f"Campaign status can only be APPROVED or NEW."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Retrieve campaign entity before update
        campaigns = Campaign.objects.all().filter(id=campaign_id)
        if campaigns is not None and len(campaigns) == 1:
            # check current campaign status
            if campaigns[0].status != "PENDING":
                return Response(
                    {
                        "message": f"Campaign already approved or reject by other people."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                # Update campaign status
                campaigns.update(
                    status=campaign_status,
                )
                return Response(
                    {
                        "message": f"Campaign status updated to {campaign_status} successfully."
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {"message": f"Campaign is not exist any more."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], name="campaign paginated query")
    def pagination(self, request, *args, **kwargs):
        """paginated query"""
        # TODO to be merged with list function if list function don't needed anymore
        queryset = Campaign.objects.all().order_by("creation_datetime")
        # Extract the request params
        tag_names = self.request.query_params.get("tag_names")
        company = self.request.query_params.get("company")
        hsbc_vs_non_hsbc = self.request.query_params.get("hsbc_vs_non_hsbc")
        message_type = self.request.query_params.get("message_type")

        # Filtering logic on hsbc_vs_non_hsbc (AND condition)
        if hsbc_vs_non_hsbc:
            queryset = queryset.filter(hsbc_vs_non_hsbc__exact=hsbc_vs_non_hsbc)

        # Filtering logic on company (AND condition)
        if company:
            queryset = queryset.filter(company__exact=company)

        # Filtering logic on message_type (AND condition)
        if message_type:
            queryset = queryset.filter(message_type__exact=message_type)

        # Filtering logic on tags (AND condition)
        if tag_names is not None and tag_names != "":
            # Extract the tags filter
            tags = tag_names.split(",")

            filter_list = []
            for tag in tags:
                # Query the campaign tag linkage to get unique campaign id containing the specific tags
                tag_queryset = CampaignTagLinkage.objects.all()
                tag_queryset = tag_queryset.filter(tag_name__exact=tag)
                campaign_ids = list(
                    set([int(campaign.campaign_id) for campaign in tag_queryset])
                )
                filter_list.append(campaign_ids)

            result_campadign_ids = set(filter_list[0])
            if len(filter_list) > 1:
                for s in filter_list[1:]:
                    result_campadign_ids.intersection_update(s)

            result_campadign_ids = list(result_campadign_ids)
            # Filter campaign by campaign id
            queryset = queryset.filter(pk__in=result_campadign_ids)

        # pagnation
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        # Converting the image path into images
        for record in serializer.data:
            image_path = record["campaign_thumbnail_url"]
            img = PILImage.open(image_path)
            buf = io.BytesIO()
            image_type = image_path.split(".")[1]

            if image_type.lower() in ("jpg", "jpeg"):
                img.save(buf, format="JPEG")
            elif image_type.lower() == "png":
                img.save(buf, format="PNG")
            else:
                print(f"Unsupport image type ")

            byte_im = base64.b64encode(buf.getvalue())
            record["img"] = byte_im

        return self.get_paginated_response(serializer.data)

    # def destroy(self, request, *args, **kwargs):

    #     # delete campaign
    #     campaign = self.get_object()
    #     self.perform_destroy(campaign)

    #     print(campaign.id)

    #     image_queryset = Image.objects.all().filter(campaign_id__exat = campaign.id)
    #     print(image_queryset)

    #     return Response(
    #         {"message": f"deleted"},
    #         status=status.HTTP_200_OK,
    #     )


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
        tag_names = self.request.query_params.get("tag_names")
        queryset = Image.objects.all()

        # Filter by tag names if tag_names is passed (AND condition)
        if tag_names:
            tags = tag_names.split(",")

            filter_list = []
            for tag in tags:
                # Query the campaign tag linkage to get unique campaign id containing the specific tags
                campaign_linkage_query_set = CampaignTagLinkage.objects.all().filter(
                    tag_name__exact=tag
                )
                campaign_id_list = list(
                    set(
                        [
                            int(campaign.campaign_id)
                            for campaign in campaign_linkage_query_set
                        ]
                    )
                )
                filter_list.append(campaign_id_list)

            result_campadign_ids = set(filter_list[0])
            if len(filter_list) > 1:
                for s in filter_list[1:]:
                    result_campadign_ids.intersection_update(s)
            result_campadign_ids = list(result_campadign_ids)

            queryset = queryset.filter(campaign_id__in=result_campadign_ids)

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
        campaign_id = request.data["campaign_id"]

        # Define the path to save images and thumbnail
        image_tmp_path = "static/" + str(image)
        image_path = "static/images/" + str(image)
        image_thumbnail_path = "static/image_thumbnail/" + str(image)

        # Process the image
        image_file_io = io.BytesIO(image.file.read())
        image_file = PILImage.open(image_file_io)

        # Saving image to the static file
        image_file.save(image_tmp_path)

        # Saving the image meta data
        image_width, image_height = image_file.size
        image_type = str(image).split(".")[-1]

        # Get size of image after saving
        image_size = str(os.path.getsize(image_tmp_path) / 1024) + " KB"

        # Calc image hash
        image_hash = self._md5(image_tmp_path)

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
            # Saving the actual images and remove the tmp image file
            image_file.save(image_path)
            os.remove(image_tmp_path)

            # generate thumbnail file
            image_thumbnail_file = expand2square(image_file, "white").resize(
                THUMBNAIL_SIZE
            )

            # Saving image once all validation is done
            image_thumbnail_file.save(image_thumbnail_path)

            image = Image(
                image_name=image_name,
                image_type=image_type,
                image_size=image_size,
                image_width=image_width,
                image_height=image_height,
                image_url=image_path,
                image_hash=image_hash,
                campaign_id=campaign_id,
                image_thumbnail_url=image_thumbnail_path,
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
