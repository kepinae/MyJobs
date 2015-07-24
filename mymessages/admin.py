from django import forms
from django.contrib import admin

from mymessages.models import Message


class AdminMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = '__all__'


class AdminMessage(admin.ModelAdmin):
    form = AdminMessageForm
    list_display = ('subject', 'start_on', 'expire_at')
    fieldsets = (
        ('Send to', {
            'fields': (
                'group',
            ),
        }),
        ('Message', {
            'fields': (
                'message_type', 'subject', 'body', 'btn_text', 'system',
            ),
        }),
        (None, {
            'fields': (
                'start_on', 'expire_at',
            )
        })
    )


admin.site.register(Message, AdminMessage)
