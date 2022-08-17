from django.contrib import admin

from .models import Image, Tag, CampaignTagLinkage,Campaign

admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(CampaignTagLinkage)
admin.site.register(Campaign)
