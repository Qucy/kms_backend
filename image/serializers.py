from rest_framework import serializers
from .models import Image, Tag, CampaignTagLinkage, Campaign


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = [
            "id",
            "image_name",
            "image_type",
            "image_size",
            "image_width",
            "image_height",
            "image_url",
            "image_hash",
            "image_thumbnail_url",
            "image_hash",
            "campaign_id",
            "create_by",
            "creation_datetime",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "tag_name", "tag_category", "create_by", "creation_datetime"]


class CampaignTagLinkageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignTagLinkage
        fields = ["id", "campaign_id", "tag_name", "creation_datetime"]


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "company",
            "hsbc_vs_non_hsbc",
            "location",
            "message_type",
            "response_rate",
            "campaign_thumbnail_url",
            "create_by",
            "creation_datetime",
            "status",
        ]
