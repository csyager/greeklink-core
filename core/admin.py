from django.contrib import admin
from django.conf import settings
from django.conf.urls import url
from django.core.mail import send_mass_mail
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from core.models import *
from .forms import InviteUsersForm, SiteSettingsForm

# Register your models here.
admin.site.register(ResourceFile)
admin.site.register(SocialEvent)
admin.site.register(Announcement)
admin.site.register(ResourceLink)
admin.site.register(Attendee)
admin.site.register(Roster)
admin.site.register(RosterMember)

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

admin.site.site_header = "Greek-Rho Settings"

class UserOpts():
    object_name = "user"
    app_label = "auth"
    model_name = "user"

class UserAdmin(admin.ModelAdmin):
    change_list_template = "admin/user_change_list.html"

    def get_urls(self):
        base_urls = super(UserAdmin, self).get_urls()
        additional_urls = [
            url(r'^invite/$', self.admin_site.admin_view(self.invitation_configuration)),
            url(r'^invite/send$', self.admin_site.admin_view(self.send_invitations))
        ]
        return additional_urls + base_urls
    
    def invitation_configuration(self, request):
        context = dict(
            self.admin_site.each_context(request),
            add = False,
            change = False,
            save_as = False,
            has_add_permission = False,
            has_change_permission = False,
            has_view_permission = False,
            opts = UserOpts,
            invite_users_form = InviteUsersForm
        )
        return TemplateResponse(request, "admin/user_invitation.html", context)

    def send_invitations(self, request):
        if request.method == 'POST':
            recipients = request.POST.get('recipients')
            message_list = []
            tenant_name = request.tenant.name
            title = f"Join {tenant_name} on GreekRho!"
            truemessage = render_to_string('admin/invitation_email.html', {
                'user': request.user.first_name + ' ' + request.user.last_name,
                'organization': tenant_name,
                'target': "https://" + request.tenant.domain_url + "/signup"
            })
            recipient_count = 0
            for recipient in recipients.splitlines():
                if recipient != "":
                    recipient_count += 1
                    message_list.append((title, truemessage, settings.EMAIL_HOST_USER, [recipient]))
            send_mass_mail(message_list, fail_silently=True, auth_user=settings.EMAIL_HOST_USER)
            messages.success(request, f"Success!  Email invitation has been sent to {recipient_count} recipients.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            raise Http404
  
admin.site.unregister(User)
admin.site.register(User, UserAdmin)