# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileUnits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('date_updated', models.DateTimeField(default=datetime.datetime.now, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Name',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('given_name', models.CharField(max_length=30, verbose_name='first name')),
                ('family_name', models.CharField(max_length=30, verbose_name='last name')),
                ('primary', models.BooleanField(default=False, verbose_name='Is primary name?')),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='MilitaryService',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('country_code', models.CharField(max_length=3, verbose_name='Country', blank=True)),
                ('branch', models.CharField(max_length=255, verbose_name=b'Branch')),
                ('department', models.CharField(max_length=255, verbose_name=b'Department', blank=True)),
                ('division', models.CharField(max_length=255, verbose_name=b'Division', blank=True)),
                ('expertise', models.CharField(max_length=255, verbose_name=b'Expertise', blank=True)),
                ('service_start_date', models.DateField(null=True, verbose_name='Start Date', blank=True)),
                ('service_end_date', models.DateField(null=True, verbose_name='End Date', blank=True)),
                ('start_rank', models.CharField(max_length=50, verbose_name='Start Rank', blank=True)),
                ('end_rank', models.CharField(max_length=50, verbose_name='End Rank', blank=True)),
                ('campaign', models.CharField(max_length=255, verbose_name=b'Campaign', blank=True)),
                ('honor', models.CharField(max_length=255, verbose_name=b'Honors', blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('license_name', models.CharField(max_length=255, verbose_name=b'License Name')),
                ('license_type', models.CharField(max_length=255, verbose_name=b'License Type')),
                ('description', models.CharField(max_length=255, verbose_name=b'Description', blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='EmploymentHistory',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('position_title', models.CharField(max_length=255, verbose_name='Position Title')),
                ('organization_name', models.CharField(max_length=255, verbose_name='Company', blank=True)),
                ('start_date', models.DateField(verbose_name='Start Date')),
                ('current_indicator', models.BooleanField(default=False, verbose_name='I still work here')),
                ('end_date', models.DateField(null=True, blank=True)),
                ('city_name', models.CharField(max_length=255, null=True, blank=True)),
                ('country_sub_division_code', models.CharField(max_length=5, verbose_name='State/Region', blank=True)),
                ('country_code', models.CharField(max_length=3, null=True, verbose_name='country', blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('industry_code', models.CharField(verbose_name='industry', max_length=255, null=True, editable=False, blank=True)),
                ('job_category_code', models.CharField(verbose_name='job category', max_length=255, null=True, editable=False, blank=True)),
                ('onet_code', models.CharField(max_length=255, null=True, editable=False, blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('organization_name', models.CharField(max_length=255, verbose_name='institution', blank=True)),
                ('degree_date', models.DateField(null=True, verbose_name='completion date', blank=True)),
                ('city_name', models.CharField(max_length=255, verbose_name='city', blank=True)),
                ('country_sub_division_code', models.CharField(max_length=5, verbose_name='State/Region', blank=True)),
                ('country_code', models.CharField(max_length=3, verbose_name='country', blank=True)),
                ('education_level_code', models.IntegerField(blank=True, null=True, verbose_name='education level', choices=[(b'', 'Education Level'), (3, 'High School'), (4, 'Non-Degree Education'), (5, 'Associate'), (6, 'Bachelor'), (7, 'Master'), (8, 'Doctoral')])),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('education_score', models.CharField(max_length=255, verbose_name='GPA', blank=True)),
                ('degree_name', models.CharField(max_length=255, verbose_name='degree type', blank=True)),
                ('degree_major', models.CharField(max_length=255, verbose_name='major', blank=True)),
                ('degree_minor', models.CharField(max_length=255, verbose_name='minor', blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('label', models.CharField(max_length=60, verbose_name='Address Label', blank=True)),
                ('address_line_one', models.CharField(max_length=255, verbose_name='Address Line One', blank=True)),
                ('address_line_two', models.CharField(max_length=255, verbose_name='Address Line Two', blank=True)),
                ('city_name', models.CharField(max_length=255, verbose_name='City', blank=True)),
                ('country_sub_division_code', models.CharField(max_length=5, verbose_name='State/Region', blank=True)),
                ('country_code', models.CharField(max_length=3, verbose_name='Country', blank=True)),
                ('postal_code', models.CharField(max_length=12, verbose_name='Postal Code', blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='SecondaryEmail',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('email', models.EmailField(unique=True, max_length=255, error_messages={b'unique': b'This email is already registered.'})),
                ('label', models.CharField(max_length=30, null=True, blank=True)),
                ('verified', models.BooleanField(default=False, editable=False)),
                ('verified_date', models.DateTimeField(null=True, editable=False, blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('headline', models.CharField(help_text=b'How you describe your profession. ie "Experienced accounting professional"', max_length=100, verbose_name=b'Headline')),
                ('the_summary', models.TextField(help_text=b'A short summary of your strength and career to date.', max_length=2000, verbose_name=b'Summary', blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='Telephone',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('channel_code', models.CharField(max_length=30, editable=False, blank=True)),
                ('country_dialing', models.CharField(max_length=3, verbose_name='Country Code', blank=True)),
                ('area_dialing', models.CharField(max_length=5, verbose_name='Area Code', blank=True)),
                ('number', models.CharField(max_length=10, verbose_name='Local Number', blank=True)),
                ('extension', models.CharField(max_length=5, blank=True)),
                ('use_code', models.CharField(blank=True, max_length=30, verbose_name='Phone Type', choices=[(b'', b'Phone Type'), (b'Home', b'Home'), (b'Work', b'Work'), (b'Mobile', b'Mobile'), (b'Pager', b'Pager'), (b'Fax', b'Fax'), (b'Other', b'Other')])),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='VolunteerHistory',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('position_title', models.CharField(max_length=255, verbose_name='Position Title')),
                ('organization_name', models.CharField(max_length=255, verbose_name='Organization')),
                ('start_date', models.DateField(verbose_name='Start Date')),
                ('current_indicator', models.BooleanField(default=False, verbose_name='I still volunteer here')),
                ('end_date', models.DateField(null=True, blank=True)),
                ('city_name', models.CharField(max_length=255, blank=True)),
                ('country_sub_division_code', models.CharField(max_length=5, verbose_name='State/Region', blank=True)),
                ('country_code', models.CharField(max_length=3, verbose_name='country', blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.CreateModel(
            name='Website',
            fields=[
                ('profileunits_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='myprofile.ProfileUnits')),
                ('display_text', models.CharField(max_length=50, verbose_name=b'Display Text', blank=True)),
                ('uri', models.URLField(verbose_name=b'Web Address')),
                ('uri_active', models.BooleanField(default=False, verbose_name=b'Currently active?')),
                ('description', models.TextField(max_length=500, verbose_name=b'Site Description', blank=True)),
                ('site_type', models.CharField(blank=True, max_length=50, verbose_name=b'Type of Site', choices=[(b'personal', b'Personal'), (b'portfolio', b'Portfolio of my work'), (b'created', b'Site I created or helped create'), (b'association', b'Group or Association'), (b'social', b'Social media'), (b'other', b'Other')])),
            ],
            options={
            },
            bases=('myprofile.profileunits',),
        ),
        migrations.AddField(
            model_name='profileunits',
            name='content_type',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profileunits',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
