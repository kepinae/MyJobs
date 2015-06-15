from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model

import operator


# I don't really like doing it this way (get from database pre save, set
# attribute, get again post save), but we need to be able to 1) determine what
# was changed and 2) only send an email if the save is successful. - TP
def cron_post_save(sender, instance, **kwargs):
    """
    Finds and schedules tasks for any CronEvents bound to the given instance.

    Inputs:
    :sender: Which event type was saved
    :instance: Specific instance saved
    """
    CronEvent = get_model('myemails', 'CronEvent')
    EmailTask = get_model('myemails', 'EmailTask')
    content_type = ContentType.objects.get_for_model(sender)
    cron_event_kwargs = {'model': content_type,
                         'owner': instance.product.owner if hasattr(
                             instance, 'product') else instance.owner}
    # Gets all CronEvents for this company and model...
    events = list(CronEvent.objects.filter(**cron_event_kwargs))
    # ...and all tasks scheduled for this instance.
    tasks = EmailTask.objects.filter(
        object_id=instance.pk,
        object_model=content_type)
    triggered_events = {task_.related_event for task_ in tasks}
    for event in triggered_events:
        if event in events:
            # If an event is already scheduled, remove it from the list of
            # events to be scheduled.
            events.remove(event)
    for event in events:
        # Schedule all remaining events.
        EmailTask.objects.create(act_on=instance,
                                 related_event=event).schedule()


def value_pre_save(sender, instance, **kwargs):
    """
    Determines if a given ValueEvent bound to the provided instance has been
    triggered.

    Inputs:
    :sender: Which event type is being saved
    :instance: Specific instance being saved
    """
    ValueEvent = get_model('myemails', 'ValueEvent')
    triggered = []
    if instance.pk:
        value_event_kwargs = {
            'model': ContentType.objects.get_for_model(sender),
            'owner': instance.product.owner if hasattr(
                instance, 'product') else instance.owner}
        events = ValueEvent.objects.filter(**value_event_kwargs)
        original = sender.objects.get(pk=instance.pk)
        for event in events:
            old_val = getattr(original, event.field)
            new_val = getattr(instance, event.field)
            compare = getattr(operator, event.compare_using, 'eq')
            # This should only be triggered once when the conditions are met
            # (value <= 3 fires once value reaches 3 and does not fire again
            # when value reaches 2). Check the pre-save value in addition to
            # the post-save value to ensure this.
            if (not compare(old_val, event.value) and
                    compare(new_val, event.value)):
                triggered.append(event.pk)
    instance.triggered = triggered


def value_post_save(sender, instance, **kwargs):
    """
    Schedules any triggered events found in value_pre_save.

    Inputs:
    :sender: Which event type is being saved
    :instance: Specific instance being saved
    """
    EmailTask = get_model('myemails', 'EmailTask')
    ValueEvent = get_model('myemails', 'ValueEvent')
    if instance.triggered:
        events = ValueEvent.objects.filter(id__in=instance.triggered)
        for event in events:
            EmailTask.objects.create(act_on=instance,
                                     related_event=event).schedule()


def pre_add_invoice(sender, instance, **kwargs):
    """
    Determines if an invoice has been added to the provided instance.

    Inputs:
    :sender: Which event type is being saved
    :instance: Specific instance being saved
    """
    invoice_added = hasattr(instance, 'invoice')
    if instance.pk:
        original = sender.objects.get(pk=instance.pk)
        invoice_added = not hasattr(original, 'invoice') and invoice_added
    instance.invoice_added = invoice_added


def post_add_invoice(sender, instance, **kwargs):
    """
    Schedules tasks for the instance if pre_add_invoice determined that an
    invoice was added.

    Inputs:
    :sender: Which event type is being saved
    :instance: Specific instance being saved
    """
    CreatedEvent = get_model('myemails', 'CreatedEvent')
    EmailTask = get_model('myemails', 'EmailTask')
    if instance.invoice_added:
        content_type = ContentType.objects.get(model='invoice')
        events = CreatedEvent.objects.filter(model=content_type,
                                             owner=instance.product.owner)
        for event in events:
            EmailTask.objects.create(act_on=instance.invoice,
                                     related_event=event).schedule()
