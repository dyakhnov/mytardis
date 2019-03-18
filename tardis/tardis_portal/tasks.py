import logging

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models import Q

from tardis.celery import tardis_app
from .email import email_user


logger = logging.getLogger(__name__)


@tardis_app.task(name="tardis_portal.verify_dfos", ignore_result=True)
def verify_dfos(**kwargs):
    from .models import DataFileObject
    dfos_to_verify = DataFileObject.objects.filter(verified=False)
    kwargs['transaction_lock'] = kwargs.get('transaction_lock', True)
    for dfo in dfos_to_verify:
        kwargs['priority'] = dfo.priority
        kwargs['shadow'] = 'dfo_verify location:%s' % dfo.storage_box.name
        dfo_verify.apply_async(args=[dfo.id], **kwargs)


@tardis_app.task(name='tardis_portal.ingest_received_files', ignore_result=True)
def ingest_received_files(**kwargs):
    '''
    finds all files stored in temporary storage boxes and attempts to move
    them to their permanent home
    '''
    from .models import StorageBox
    ingest_boxes = StorageBox.objects.filter(Q(attributes__key='type'),
                                             Q(attributes__value='receiving'),
                                             ~Q(master_box=None))
    for box in ingest_boxes:
        kwargs['shadow'] = 'sbox_move_to_master location:%s' % box.name
        kwargs['priority'] = box.priority
        sbox_move_to_master.apply_async(args=[box.id], **kwargs)


@tardis_app.task(name="tardis_portal.autocache", ignore_result=True)
def autocache(**kwargs):
    from .models import StorageBox
    autocache_boxes = StorageBox.objects.filter(
        Q(attributes__key='autocache'),
        Q(attributes__value__iexact='True'))

    for box in autocache_boxes:
        kwargs['shadow'] = 'sbox_cache_files location:%s' % box.name
        kwargs['priority'] = box.priority
        sbox_cache_files.apply_async(args=[box.id], **kwargs)


@tardis_app.task(name="tardis_portal.email_user_task", ignore_result=True)
def email_user_task(subject, template_name, context, user_id):
    user = User.objects.get(id=user_id)
    email_user(subject, template_name, context, user)


@tardis_app.task(name='tardis_portal.cache_notify', ignore_result=True)
def cache_done_notify(results, user_id, site_id, ct_id, obj_ids):
    user = User.objects.get(id=user_id)
    site = Site.objects.get(id=site_id)
    subject = '[{site}] Cache recall done'.format(site=site.name)
    ct = ContentType.objects.get(id=ct_id)
    objects = [ct.get_object_for_this_type(id=obj_id) for obj_id in obj_ids]
    context = {
        'objects': objects,
        'username': user.username,
    }
    email_user(subject, 'cache_done_email', context, user)
    return "all done"


# "method tasks"
# StorageBox
@tardis_app.task(name="tardis_portal.storage_box.copy_files", ignore_result=True)
def sbox_copy_files(sbox_id, dest_box_id=None):
    from .models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return sbox.copy_files(dest_box=dest_box)


@tardis_app.task(name="tardis_portal.storage_box.move_files", ignore_result=True)
def sbox_move_files(sbox_id, dest_box_id=None):
    from .models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return sbox.move_files(dest_box=dest_box)


@tardis_app.task(name="tardis_portal.storage_box.cache_files", ignore_result=True)
def sbox_cache_files(sbox_id):
    """
    Copy all files to faster storage.

    This can be used to copy data from a Vault cache (containing data
    which will soon be pushed to tape) to Object Storage, so that the
    data can always be accessed quickly from Object Storage, and the
    Vault can be used for disaster recovery if necessary.
    """
    from .models import DataFileObject
    from .models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    shadow = 'dfo_cache_file location:%s' % sbox.name
    for dfo in DataFileObject.objects.filter(storage_box=sbox, verified=True):
        if DataFileObject.objects.filter(datafile=dfo.datafile).count() == 1:
            dfo_cache_file.apply_async(
                args=[dfo.id], priority=sbox.priority, shadow=shadow)


@tardis_app.task(name='tardis_portal.storage_box.copy_to_master', ignore_result=True)
def sbox_copy_to_master(sbox_id, *args, **kwargs):
    from .models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    return sbox.copy_to_master(*args, **kwargs)


@tardis_app.task(name='tardis_portal.storage_box.move_to_master', ignore_result=True)
def sbox_move_to_master(sbox_id, *args, **kwargs):
    from .models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    return sbox.move_to_master(*args, **kwargs)


# DataFile
@tardis_app.task(name="tardis_portal.cache_datafile", ignore_result=True)
def df_cache_file(df_id):
    from .models import DataFile
    df = DataFile.objects.get(id=df_id)
    return df.cache_file()


# DataFileObject
@tardis_app.task(name='tardis_portal.dfo.move_file', ignore_result=True)
def dfo_move_file(dfo_id, dest_box_id=None):
    from .models import DataFileObject, StorageBox
    dfo = DataFileObject.objects.get(id=dfo_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return dfo.move_file(dest_box)


@tardis_app.task(name='tardis_portal.dfo.copy_file', ignore_result=True)
def dfo_copy_file(dfo_id, dest_box_id=None):
    from .models import DataFileObject, StorageBox
    dfo = DataFileObject.objects.get(id=dfo_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return dfo.copy_file(dest_box=dest_box)


@tardis_app.task(name='tardis_portal.dfo.cache_file', ignore_result=True)
def dfo_cache_file(dfo_id):
    from .models import DataFileObject
    dfo = DataFileObject.objects.get(id=dfo_id)
    return dfo.cache_file()


@tardis_app.task(name="tardis_portal.dfo.verify", ignore_result=True)
def dfo_verify(dfo_id, *args, **kwargs):
    from .models import DataFileObject
    # Get dfo locked for write (to prevent concurrent actions)
    if kwargs.pop('transaction_lock', False):
        with transaction.atomic():
            dfo = DataFileObject.objects.select_for_update().get(id=dfo_id)
            return dfo.verify(*args, **kwargs)
    dfo = DataFileObject.objects.get(id=dfo_id)
    return dfo.verify(*args, **kwargs)


@tardis_app.task(name='tardis_portal.clear_sessions', ignore_result=True)
def clear_sessions():
    """Clean up expired sessions using Django management command."""
    from django.core import management
    management.call_command("clearsessions", verbosity=0)


@tardis_app.task(name='tardis_portal.save_metadata', ignore_result=True)
def save_metadata(id, name, schema, metadata):
    """Save all the metadata to a Dataset_Files paramamter set."""
    from fractions import Fraction
    from .models import ParameterName, Schema, DataFile,\
                        DatafileParameterSet, DatafileParameter

    def getSchema(schema, name):
        """
        Return the schema object that the paramaterset will use.
        """
        try:
            return Schema.objects.get(namespace__exact=schema)
        except Schema.DoesNotExist:
            new_schema = Schema(namespace=schema, name=name,
                                type=Schema.DATAFILE)
            new_schema.save()
            return new_schema

    def getParameters(schema, metadata):
        """
        Return a list of the paramaters that will be saved.
        """
        param_objects = ParameterName.objects.filter(schema=schema)
        parameters = []
        for p in metadata:
            parameter = filter(lambda x, y=p: x.name == y, param_objects)
            if parameter:
                parameters.append(parameter[0])
        return parameters

    data_schema = getSchema(schema, name)
    parameters = getParameters(data_schema, metadata)
    if not parameters:
        print("Bailing out of save_metadata because of 'not parameters'.")
    else:
        # Load datafile
        df = DataFile.objects.get(id=id)

        # Check for existing data
        try:
            ps = DatafileParameterSet.objects.get(schema=data_schema,
                                                  datafile=df)
            print("Parameter set already exists for {}".format(df.filename))
        except DatafileParameterSet.DoesNotExist:
            ps = DatafileParameterSet(schema=data_schema, datafile=df)
            ps.save()
            # Save metadata
            for p in parameters:
                print(p.name)
                if p.name in metadata:
                    dfp = DatafileParameter(parameterset=ps, name=p)
                    if p.isNumeric():
                        if metadata[p.name] != '':
                            dfp.numerical_value = metadata[p.name]
                            dfp.save()
                    elif isinstance(metadata[p.name], list):
                        for val in reversed(metadata[p.name]):
                            strip_val = val.strip()
                            if strip_val:
                                dfp = DatafileParameter(parameterset=ps,
                                                        name=p)
                                dfp.string_value = strip_val
                                dfp.save()
                    else:
                        dfp.string_value = metadata[p.name]
                        dfp.save()
