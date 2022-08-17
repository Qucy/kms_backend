from django.db import models


class Image(models.Model):
    """
    Image model to store image meta data
    """

    image_name = models.CharField(max_length=50)
    image_type = models.CharField(max_length=20)
    image_size = models.CharField(max_length=20)
    image_width = models.PositiveBigIntegerField(default=0)
    image_height = models.PositiveBigIntegerField(default=0)
    image_url = models.CharField(max_length=200)
    image_hash = models.CharField(max_length=64, default="")
    campaign_id = models.CharField(max_length=200)
    image_thumbnail = models.CharField(max_length=5000)
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField("datetime image uploaded", auto_now=True)
    

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["image_name"], name="image name unique constraint"
            ),
        ]

    def __str__(self) -> str:
        return self.image_name


class Tag(models.Model):
    """Tag model to store image taggings"""

    tag_name = models.CharField(max_length=200)
    tag_category = models.CharField(max_length=50)
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField("datetime tag created")

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["tag_name"], name="tag name unique constraint"
            ),
        ]

    def __str__(self) -> str:
        return self.tag_category + ":" + self.tag_name


class CampaignTagLinkage(models.Model):
    """ Linkage table to store image and tag mappings
    """
    campaign_id = models.CharField(max_length=200)
    tag_name = models.CharField(max_length=200)
    creation_datetime = models.DateTimeField('datetime linkage created')
    
    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['campaign_id', 'tag_name'], name='campaign and tag name link constraint'),
        ]

        indexes = [
            models.Index(fields=['campaign_id'], name='campaign_id_tag_idx'),
            models.Index(fields=['tag_name'], name='tag_name_idx'),
        ]

    def __str__(self) -> str:
        return self.campaign_id + "<->" + self.tag_name



class Campaign(models.Model):
    """
    Image model to store image meta data
    """
    company = models.CharField(max_length=30)
    hsbc_vs_non_hsbc = models.CharField(max_length=10)
    location = models.CharField(max_length=50)
    message_type = models.CharField(max_length=50)
    response_rate = models.CharField(max_length=200)
    campaign_thumbnail_url = models.CharField(max_length=200)
    creation_datetime = models.DateTimeField('datetime image uploaded', auto_now=True)


    def __str__(self) -> str:
        return self.company + "<->" + self.location + "<->" + self.message_type + "<->" + self.creation_datetime
