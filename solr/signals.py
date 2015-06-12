import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete, pre_save

from myjobs.models import User
from myprofile.models import ProfileUnits
from mysearches.models import SavedSearch
from solr.models import Update

logging.basicConfig()
logger = logging.getLogger(__name__)


def presave_solr(sender, instance, *args, **kwargs):
    """
    Flag an instance for being uploaded to solr in the post-save if anything
    we actually care about has been changed.

    """
    ignore_fields = ['last_response', 'last_sent', 'date_updated',
                     'last_login', 'date_joined']
    setattr(instance, 'solr_update', False)
    if instance.pk:
        # The instance might have a pk but still not actually
        # exist (eg: loading fixtures).
        try:
            obj = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            setattr(instance, 'solr_update', True)
            return

        for field in obj._meta.fields:
            current_val = getattr(obj, field.attname)
            new_val = getattr(instance, field.attname)
            try:
                if field.attname not in ignore_fields and current_val != new_val:
                    setattr(instance, 'solr_update', True)
            except TypeError, e:
                logger.error("%s for field %s" % (e, field.attname))
                setattr(instance, 'solr_update', True)
    else:
        setattr(instance, 'solr_update', True)


def prepare_add_to_solr(sender, instance, **kwargs):
    """
    Converts an object instance into a dictionary and adds it to solr.

    """
    if getattr(instance, 'solr_update', None):
        if sender in ProfileUnits.__subclasses__():
            content_type_id = ContentType.objects.get_for_model(ProfileUnits).pk
            object_id = instance.user_id
        else:
            content_type_id = ContentType.objects.get_for_model(sender).pk
            object_id = instance.pk
        uid = "%s##%s" % (content_type_id, object_id)

        obj, _ = Update.objects.get_or_create(uid=uid)
        obj.delete = False
        obj.save()


def prepare_delete_from_solr(sender, instance, **kwargs):
    """
    Removes and object instance from solr.

    """
    if sender in ProfileUnits.__subclasses__():
        content_type_id = ContentType.objects.get_for_model(ProfileUnits).pk
        object_id = instance.user_id

        # If there are existing ProfileUnits for a user, since all ProfileUnits
        # are in the same solr document, update the document rather than
        # removing it.
        if ProfileUnits.objects.filter(user_id=instance.user_id).exclude(
                pk=instance.pk):
            prepare_add_to_solr(sender, instance, **kwargs)
            return
    else:
        content_type_id = ContentType.objects.get_for_model(sender).pk
        object_id = instance.pk
    uid = "%s##%s" % (content_type_id, object_id)
    obj, _ = Update.objects.get_or_create(uid=uid)
    obj.delete = True
    obj.save()


def profileunits_to_dict(user_id):
    """
    Creates a dictionary of profile units for a user.

    inputs:
    :user_id: the id of the user the dictionary is being created for

    """
    content_type_id = ContentType.objects.get_for_model(ProfileUnits).pk
    solr_dict = {
        'uid': "%s##%s" % (content_type_id, user_id),
        'ProfileUnits_user_id': user_id,
    }
    models = {}

    units = ProfileUnits.objects.filter(user_id=user_id).select_related('name',
                                                                        'education',
                                                                        'website',
                                                                        'telephone',
                                                                        'address',
                                                                        'secondaryemail',
                                                                        'militaryservice',
                                                                        'license',
                                                                        'summary',
                                                                        'employmenthistory',
                                                                        'volunteerhistory',
                                                                        'content_type')
    for unit in units:
        unit = getattr(unit, unit.get_model_name())
        models.setdefault(unit.__class__.__name__, []).append(unit)

    for model_name, objs in models.items():
        if not objs:
            continue

        if model_name == 'Address':
            solr_dict['Address_region'] = ["%s##%s" %
                                           (getattr(obj, 'country_code'),
                                            getattr(obj, 'country_sub_division_code'))
                                           for obj in objs]
            solr_dict['Address_full_location'] = ["%s##%s##%s" %
                                                  (getattr(obj, 'country_code'),
                                                   getattr(obj, 'country_sub_division_code'),
                                                   getattr(obj, 'city_name'))
                                                  for obj in objs]
        for field in objs[0]._meta.fields:
            obj_list = [getattr(obj, field.attname) for obj in objs]
            field_type = field.get_internal_type()
            if (field_type != 'OneToOneField' and
                    not any(s in field.attname
                            for s in ['password', 'timezone',
                                      'deactivate_type'])):
                field_name = "%s_%s" % (model_name, field.attname)
                solr_dict[field_name] = filter(None, list(obj_list))

    return solr_dict


def object_to_dict(model, obj):
    """
    Turns an object into a solr compatible dictionary.

    inputs:
    :model: the model for the object
    :object: object being converted into a solr dictionary

    """
    content_type_id = ContentType.objects.get_for_model(model).pk
    object_id = obj.pk
    solr_dict = {
        'uid': "%s##%s" % (content_type_id, object_id),
    }

    if model == SavedSearch:
        if obj.user:
            solr_dict['SavedSearch_company_id'] = obj.get_company()

            for field in User._meta.fields:
                field_type = field.get_internal_type()
                if (field_type != 'OneToOneField' and
                        not any(s in field.attname
                                for s in ['password', 'timezone',
                                          'deactivate_type'])):
                    field_name = "User_%s" % field.attname
                    solr_dict[field_name] = getattr(obj.user, field.attname)
        else:
            return None

    for field in model._meta.fields:
        field_type = field.get_internal_type()
        if (field_type != 'OneToOneField' and
                not any(s in field.attname
                        for s in ['password', 'timezone',
                                  'deactivate_type'])):
            field_name = "%s_%s" % (model.__name__, field.attname)
            solr_dict[field_name] = getattr(obj, field.attname)
    return solr_dict


post_save.connect(prepare_add_to_solr, sender=User,
                  dispatch_uid="user")
post_delete.connect(prepare_delete_from_solr, sender=User,
                    dispatch_uid='user')
pre_save.connect(presave_solr, sender=User)

post_save.connect(prepare_add_to_solr, sender=SavedSearch,
                  dispatch_uid='savedsearch')
post_delete.connect(prepare_delete_from_solr, sender=SavedSearch,
                    dispatch_uid='savedsearch')
pre_save.connect(presave_solr, sender=SavedSearch)

for model_class in ProfileUnits.__subclasses__():
    pre_save.connect(presave_solr, sender=model_class)
    post_save.connect(prepare_add_to_solr,
                      sender=model_class,
                      dispatch_uid="att_post_save_"+model_class.__name__)
    post_delete.connect(prepare_delete_from_solr,
                      sender=model_class,
                      dispatch_uid="att_post_save_"+model_class.__name__)