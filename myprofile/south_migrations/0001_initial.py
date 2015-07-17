# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ProfileUnits'
        db.create_table(u'myprofile_profileunits', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myjobs.User'])),
        ))
        db.send_create_signal(u'myprofile', ['ProfileUnits'])

        # Adding model 'Name'
        db.create_table(u'myprofile_name', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('given_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('family_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('primary', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'myprofile', ['Name'])

        # Adding model 'Education'
        db.create_table(u'myprofile_education', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('organization_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('degree_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('city_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('country_sub_division_code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('education_level_code', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('education_score', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('degree_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('degree_major', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('degree_minor', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['Education'])

        # Adding model 'Address'
        db.create_table(u'myprofile_address', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('address_line_one', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('address_line_two', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('city_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('country_sub_division_code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=12, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['Address'])

        # Adding model 'Telephone'
        db.create_table(u'myprofile_telephone', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('channel_code', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('country_dialing', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('area_dialing', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('extension', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('use_code', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['Telephone'])

        # Adding model 'EmploymentHistory'
        db.create_table(u'myprofile_employmenthistory', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('position_title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('organization_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('current_indicator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('city_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('country_sub_division_code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('industry_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('job_category_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('onet_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['EmploymentHistory'])

        # Adding model 'SecondaryEmail'
        db.create_table(u'myprofile_secondaryemail', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('verified', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('verified_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['SecondaryEmail'])

        # Adding model 'MilitaryService'
        db.create_table(u'myprofile_militaryservice', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('department', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('division', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('expertise', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('service_start_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('service_end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('start_rank', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('end_rank', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('campaign', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('honor', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['MilitaryService'])

        # Adding model 'Website'
        db.create_table(u'myprofile_website', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('display_text', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('uri', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('uri_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=500, blank=True)),
            ('site_type', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['Website'])

        # Adding model 'License'
        db.create_table(u'myprofile_license', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('license_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('license_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['License'])

        # Adding model 'Summary'
        db.create_table(u'myprofile_summary', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('headline', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('the_summary', self.gf('django.db.models.fields.TextField')(max_length=2000, blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['Summary'])

        # Adding model 'VolunteerHistory'
        db.create_table(u'myprofile_volunteerhistory', (
            (u'profileunits_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myprofile.ProfileUnits'], unique=True, primary_key=True)),
            ('position_title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('organization_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('current_indicator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('city_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('country_sub_division_code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'myprofile', ['VolunteerHistory'])


    def backwards(self, orm):
        # Deleting model 'ProfileUnits'
        db.delete_table(u'myprofile_profileunits')

        # Deleting model 'Name'
        db.delete_table(u'myprofile_name')

        # Deleting model 'Education'
        db.delete_table(u'myprofile_education')

        # Deleting model 'Address'
        db.delete_table(u'myprofile_address')

        # Deleting model 'Telephone'
        db.delete_table(u'myprofile_telephone')

        # Deleting model 'EmploymentHistory'
        db.delete_table(u'myprofile_employmenthistory')

        # Deleting model 'SecondaryEmail'
        db.delete_table(u'myprofile_secondaryemail')

        # Deleting model 'MilitaryService'
        db.delete_table(u'myprofile_militaryservice')

        # Deleting model 'Website'
        db.delete_table(u'myprofile_website')

        # Deleting model 'License'
        db.delete_table(u'myprofile_license')

        # Deleting model 'Summary'
        db.delete_table(u'myprofile_summary')

        # Deleting model 'VolunteerHistory'
        db.delete_table(u'myprofile_volunteerhistory')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'myjobs.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deactivate_type': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '11'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'gravatar': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'last_response': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'opt_in_employers': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'opt_in_myjobs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password_change': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'profile_completion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "'https://secure.my.jobs'", 'max_length': '255'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'user_guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"})
        },
        u'myprofile.address': {
            'Meta': {'object_name': 'Address', '_ormbases': [u'myprofile.ProfileUnits']},
            'address_line_one': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line_two': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'city_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'country_sub_division_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myprofile.education': {
            'Meta': {'object_name': 'Education', '_ormbases': [u'myprofile.ProfileUnits']},
            'city_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'country_sub_division_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'degree_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'degree_major': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'degree_minor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'degree_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'education_level_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'education_score': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'organization_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'myprofile.employmenthistory': {
            'Meta': {'object_name': 'EmploymentHistory', '_ormbases': [u'myprofile.ProfileUnits']},
            'city_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'country_sub_division_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'current_indicator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'industry_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'job_category_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'onet_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'organization_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'position_title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        u'myprofile.license': {
            'Meta': {'object_name': 'License', '_ormbases': [u'myprofile.ProfileUnits']},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'license_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'license_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myprofile.militaryservice': {
            'Meta': {'object_name': 'MilitaryService', '_ormbases': [u'myprofile.ProfileUnits']},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'campaign': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'division': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'end_rank': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'expertise': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'honor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'service_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'service_start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'start_rank': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'myprofile.name': {
            'Meta': {'object_name': 'Name', '_ormbases': [u'myprofile.ProfileUnits']},
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myprofile.profileunits': {
            'Meta': {'object_name': 'ProfileUnits'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myjobs.User']"})
        },
        u'myprofile.secondaryemail': {
            'Meta': {'object_name': 'SecondaryEmail', '_ormbases': [u'myprofile.ProfileUnits']},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'myprofile.summary': {
            'Meta': {'object_name': 'Summary', '_ormbases': [u'myprofile.ProfileUnits']},
            'headline': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'the_summary': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'})
        },
        u'myprofile.telephone': {
            'Meta': {'object_name': 'Telephone', '_ormbases': [u'myprofile.ProfileUnits']},
            'area_dialing': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'channel_code': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'country_dialing': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'use_code': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        u'myprofile.volunteerhistory': {
            'Meta': {'object_name': 'VolunteerHistory', '_ormbases': [u'myprofile.ProfileUnits']},
            'city_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'country_sub_division_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'current_indicator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'organization_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'position_title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        u'myprofile.website': {
            'Meta': {'object_name': 'Website', '_ormbases': [u'myprofile.ProfileUnits']},
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500', 'blank': 'True'}),
            'display_text': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'profileunits_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myprofile.ProfileUnits']", 'unique': 'True', 'primary_key': 'True'}),
            'site_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'uri': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'uri_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['myprofile']