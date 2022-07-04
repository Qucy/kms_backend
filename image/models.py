from django.db import models


class Image(models.Model):
    """
    Image model to store image meta data
    """
    image_namme = models.CharField(max_length=50)
    image_type = models.CharField(max_length=20)
    image_size = models.PositiveBigIntegerField(default=0)
    image_width = models.PositiveBigIntegerField(default=0)
    image_height = models.PositiveBigIntegerField(default=0)
    image_url = models.CharField(max_length=200)
    image_desc = models.CharField(max_length=200)
    image_thumbnail = models.BinaryField()
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField('datetime image uploaded')

    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['image_namme'], name='image name unique constraint'),
        ]


    def __str__(self) -> str:
        return self.image_namme


class Tag(models.Model):
    """ Tag model mapping to tag table to store t
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
    image_id = models.IntegerField()
    tag_id = models.IntegerField()
    create_by = models.CharField(max_length=10)
    creation_datetime = models.DateTimeField('datetime linkage created')
    
    class Meta:

        constraints = [
            models.UniqueConstraint(fields=['image_id', 'tag_id'], name='image and tag link constraint'),
        ]

        indexes = [
            models.Index(fields=['image_id'], name='image_id_idx'),
            models.Index(fields=['tag_id'], name='tag_id_idx'),
        ]

    def __str__(self) -> str:
        return self.image_id + "<->" + self.tag_id




