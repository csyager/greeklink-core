from django.contrib import admin
from core.models import *
from .forms import SiteSettingsForm

# Register your models here.
admin.site.register(ResourceFile)
admin.site.register(SocialEvent)
admin.site.register(Announcement)

# registers SiteSettings object without adding to admin page
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm
    fieldsets = (
        (None, {
            'fields': ('site_title', 'primary_color_theme', 'calendar_embed', 'verification_key', 'organization_name', 'rush_signin_active')
        }),
    )
    def get_model_perms(self, request):
        return {}

admin.site.register(SiteSettings, SiteSettingsAdmin)

admin.site.site_header = "GreekLink Settings"