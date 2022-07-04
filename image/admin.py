from django.contrib import admin

from .models import Image, Tag, ImageTagLinkage

admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(ImageTagLinkage)
