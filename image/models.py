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
    image_desc = models.CharField(max_length=200)
    image_thumbnail = models.BinaryField()
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField('datetime image uploaded', auto_now=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['image_name'], name='image name unique constraint'),
        ]


    def __str__(self) -> str:
        return self.image_name


class Tag(models.Model):
    """ Tag model to store image taggings
    """
    tag_name = models.CharField(max_length=200)
    tag_category = models.CharField(max_length=50)
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField('datetime tag created')

    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['tag_name'], name='tag name unique constraint'),
        ]

    def __str__(self) -> str:
        return self.tag_category + ":" + self.tag_name


class ImageTagLinkage(models.Model):
    """ Linkage table to store image and tag mappings
    """
    image_name = models.CharField(max_length=200, default="default_image_name")
    tag_name = models.CharField(max_length=200, default="default_tag_name")
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField('datetime linkage created')
    
    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['image_name', 'tag_name'], name='image and tag name link constraint'),
        ]

        indexes = [
            models.Index(fields=['image_name'], name='image_name_idx'),
            models.Index(fields=['tag_name'], name='tag_name_idx'),
        ]

    def __str__(self) -> str:
        return self.image_name + "<->" + self.tag_name




