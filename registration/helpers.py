import json
from os import path
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core import management

from myblocks import models


def create_login_page():
    """
    Creates a login page using Blocks for the current site.
    """
    with open(path.join(settings.PROJ_ROOT,
                        'myblocks/fixtures/login_page.json')) as block_fixture:
        # Fixtures specify ids in them. As these ids probably have been used
        # already, we need to change them. We'll start by reading and parsing
        # the json fixture.
        contents = json.loads(block_fixture.read())
    created_page = None
    # The fixture contains the keys below in the "model" key of each object
    # to be created. The values below are used to map this key to the exact
    # model class.
    model_map = {'myblocks.loginblock': {'model': models.LoginBlock},
                 'myblocks.contentblock': {'model': models.ContentBlock},
                 'myblocks.registrationblock': {'model':
                                                models.RegistrationBlock},
                 'myblocks.columnblock': {'model': models.ColumnBlock},
                 'myblocks.block': {'model': models.Block},
                 'myblocks.row': {'model': models.Row},
                 'myblocks.page': {'model': models.Page},
                 'myblocks.blockorder': {'model': models.BlockOrder},
                 'myblocks.roworder': {'model': models.RowOrder},
                 'myblocks.columnblockorder': {'model':
                                               models.ColumnBlockOrder}}

    for model_str, model_dict in model_map.items():
        # Find the latest PK for each model.
        model = model_dict['model']
        if model_str.endswith('block'):
            # If we don't do this, we could end up with duplicate IDs.
            # Example: the latest ContentBlock has a PK of 1 but there is also
            # a LoginBlock with a PK of 2. If we blindly increment the
            # ContentBlock PK, we'll run into an existing row. These both are
            # subclasses of Block so we can get the latest Block's PK and
            # ensure no conflicts.
            model = model_map['myblocks.block']['model']
        latest = model.objects.order_by('-pk').first()
        model_dict['latest'] = latest.pk if latest else 1

    for thing in contents:
        # Modify the pk in the fixture to be beyond the latest value in the db.
        thing['pk'] += model_map[thing['model']]['latest']

        if thing['model'] == 'myblocks.page':
            # The default site is jobs.directemployers.org. Update this to be
            # the current site.
            thing['fields']['sites'] = [settings.SITE.pk]

            # We'll use this later to return the created page.
            created_page = thing['pk']

        # This should work but blocks are sometimes not created.
        # The more verbose code below, which should be identical to this loop
        # if unrolled, works every time.
        #for field in ['block', 'row', 'column_block', 'page']:
        #    if field in thing['fields']:
        #        model = 'myblocks.' + field.replace('_', '')
        #        thing['fields'][field] += model_map[model]['latest']

        # Update the following foreign key fields to match what we did earlier.
        if 'block' in thing['fields']:
            thing['fields']['block'] += model_map['myblocks.block']['latest']
        if 'row' in thing['fields']:
            thing['fields']['row'] += model_map['myblocks.row']['latest']
        if 'column_block' in thing['fields']:
            thing['fields']['column_block'] += model_map[
                'myblocks.columnblock']['latest']
        if 'page' in thing['fields']:
            thing['fields']['page'] += model_map['myblocks.page']['latest']

    # Re-dump this updated fixture as json.
    contents = json.dumps(contents)
    with NamedTemporaryFile(suffix='.json') as fixture:
        # Write this new text as a temp file and flush its buffer. In testing,
        # we would sometimes get truncated files without the flush().
        fixture.write(contents)
        fixture.file.flush()

        # Finally, load the fixture.
        management.call_command('loaddata', fixture.name, verbosity=0)
    if created_page is not None:
        return models.Page.objects.get(pk=created_page)