# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myemails', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='valueevent',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='valueevent',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='body',
            field=models.ForeignKey(related_name='body_for', to='myemails.EmailSection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='footer',
            field=models.ForeignKey(related_name='footer_for', to='myemails.EmailSection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='header',
            field=models.ForeignKey(related_name='header_for', to='myemails.EmailSection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='owner',
            field=models.ForeignKey(blank=True, to='seo.Company', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtask',
            name='event_model',
            field=models.ForeignKey(related_name='email_type', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailtask',
            name='object_model',
            field=models.ForeignKey(related_name='email_model', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailsection',
            name='owner',
            field=models.ForeignKey(blank=True, to='seo.Company', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cronevent',
            name='email_template',
            field=models.ForeignKey(to='myemails.EmailTemplate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cronevent',
            name='model',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cronevent',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cronevent',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='createdevent',
            name='email_template',
            field=models.ForeignKey(to='myemails.EmailTemplate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='createdevent',
            name='model',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='createdevent',
            name='owner',
            field=models.ForeignKey(to='seo.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='createdevent',
            name='sites',
            field=models.ManyToManyField(to='seo.SeoSite'),
            preserve_default=True,
        ),
    ]
