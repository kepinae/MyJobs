from django.apps import AppConfig
from django.contrib.auth.models import ContentType
from django.db.models.signals import pre_save, post_save

from myemails.models import (ALL_EVENT_MODELS, CRON_EVENT_MODELS,
                             VALUE_EVENT_MODELS, CREATED_EVENT_MODELS)
from myemails.signals import (
    cron_post_save, value_pre_save, value_post_save,  post_add_invoice,
    pre_add_invoice
)
from django.db import models, OperationalError, ProgrammingError

# The receivers used are defined in myemails.signals but bound here. If they
# were to be bound in myemails.signals as well, we would have a few interesting
# and infuriating import issues.
bind_events = lambda model, type_, sender, pre=None, post=None: [
    pre_save.connect(pre, sender=sender,
                     dispatch_uid='pre_save__%s_%s' % (
                         model, type_)) if pre else None,
    post_save.connect(post, sender=sender,
                      dispatch_uid='post_save__%s_%s' % (
                          model, type_)) if post else None]
"""
Binds the provided sender to pre_save and post_save signals.

Inputs:
:type_: Type of event being bound (cron, value, created)
:sender: Model being bound
:pre: Method to be bound to the pre_save signal; default: None
:post: Method to be bound to the post_save signal; default: None
"""


class MyEmailsConfig(AppConfig):
    name = 'myemails'

    def ready(self):
        model_map = {}
        try:
            for model in ALL_EVENT_MODELS:
                # Invoice is a foreign key on PurchasedProduct; if we're looking
                # at an invoice, bind signals on purchased product instead.
                content_type = model if model != 'invoice' else 'purchasedproduct'
                model_map[model] = ContentType.objects.get(
                    model=content_type).model_class()
        except (OperationalError, ProgrammingError):
            # We're running syncdb and the ContentType table doesn't exist yet
            pass
        else:
            for model, Model in model_map.items():
                if model in CRON_EVENT_MODELS:
                    bind_events(model, 'cron', Model, post=cron_post_save)
                if model in VALUE_EVENT_MODELS:
                    bind_events(model, 'value', Model, value_pre_save, value_post_save)
                if model in CREATED_EVENT_MODELS:
                    if model == 'invoice':
                        bind_events(model, 'created', Model, pre_add_invoice,
                                    post_add_invoice)
                    else:
                        # There are no other valid models for this choice, but there
                        # likely will be in the future. I'm not writing something that
                        # will certainly be wrong, so let's put it off until it's
                        # relevant. - TP
                        raise NotImplementedError('Add some signals for %s!' % model)

