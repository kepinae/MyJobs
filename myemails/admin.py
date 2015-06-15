from django.contrib import admin

from myemails import models
from myemails.forms import EventFieldForm


class RequestAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(RequestAdmin, self).get_form(request, obj, **kwargs)

        class AdminFormWithRequest(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)

        return AdminFormWithRequest


class CronEventAdmin(RequestAdmin):
    fieldsets = [
        ('', {
            'fields': [
                'name',
                'email_template',
                'is_active',
                'owner',
                'sites',
            ]
        }),
        ('Comparison', {
            'description': (
                'Send an email relative to some time period, e.g. a number '
                'of hours (in minutes) before a purchased product expires. '
                'Positive values indicate that an email should be sent after '
                'the time period has occurred (30 minutes after expiration) '
                'while negative values mean before that time has passed (30 '
                'minutes before expiration). The current options are for '
                'demonstration purposes only and may not be appropriate for '
                'actual events.'
            ),
            'fields': [
                'model',
                ('field', 'minutes'),
            ]
        }),
    ]
    form = EventFieldForm

    class Media:
        js = (
            'emails.js',
        )


class ValueEventAdmin(RequestAdmin):
    fieldsets = [
        ('', {
            'fields': [
                'name',
                'email_template',
                'is_active',
                'owner',
                'sites',
            ]
        }),
        ('Comparison', {
            'description': (
                'Send an email once a given criteria has been met. '
                'For example, entering "purchased product", "jobs_remaining", '
                '"is equal to", and "0" will be parsed as "send an email '
                'when someone has used up all of their allotted job postings."'
            ),
            'fields': [
                'model',
                ('field', 'compare_using', 'value'),
            ]
        }),
    ]
    form = EventFieldForm

    class Media:
        js = (
            'emails.js',
        )

admin.site.register(models.CronEvent, CronEventAdmin)
admin.site.register(models.ValueEvent, ValueEventAdmin)
admin.site.register(models.CreatedEvent)
admin.site.register(models.EmailTemplate)
admin.site.register(models.EmailSection)
