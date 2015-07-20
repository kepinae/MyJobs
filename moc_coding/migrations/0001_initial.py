# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomCareer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Custom Military/Civilian Career Map',
                'verbose_name_plural': 'Custom Military/Civilian Career Maps',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Moc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=20, db_index=True)),
                ('branch', models.CharField(max_length=11)),
                ('title', models.CharField(max_length=300)),
                ('title_slug', models.SlugField(max_length=300)),
            ],
            options={
                'ordering': ['branch', 'code'],
                'verbose_name': 'Military Occupational Code/Rating',
                'verbose_name_plural': 'Military Occupational Codes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MocDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('primary_value', models.CharField(max_length=255)),
                ('service_branch', models.CharField(max_length=2, choices=[('f', 'Air Force'), ('a', 'Army'), ('c', 'Coast Guard'), ('m', 'Marines'), ('n', 'Navy')])),
                ('military_description', models.CharField(max_length=255)),
                ('civilian_description', models.CharField(max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Onet',
            fields=[
                ('title', models.CharField(max_length=300)),
                ('code', models.CharField(max_length=10, serialize=False, primary_key=True)),
            ],
            options={
                'verbose_name': 'Onet',
                'verbose_name_plural': 'Onets',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='onet',
            unique_together=set([('title', 'code')]),
        ),
        migrations.AddField(
            model_name='moc',
            name='moc_detail',
            field=models.OneToOneField(null=True, to='moc_coding.MocDetail'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='moc',
            name='onets',
            field=models.ManyToManyField(to='moc_coding.Onet'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='moc',
            unique_together=set([('code', 'branch')]),
        ),
        migrations.AddField(
            model_name='customcareer',
            name='moc',
            field=models.ForeignKey(verbose_name=b'Military Occupational Code', to='moc_coding.Moc', help_text=b'Sorted by branch, then MOC, then MOC                             title.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customcareer',
            name='onet',
            field=models.ForeignKey(verbose_name=b'O*NET-SOC', to='moc_coding.Onet', help_text=b'Standard occupational classifications                              developed by the US Dept. of Labor.'),
            preserve_default=True,
        ),
    ]
