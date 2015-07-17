# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'DestinationManipulation', fields ['action_type', 'value_1', 'value_2', 'buid', 'view_source', 'action']
        db.delete_unique(u'redirect_destinationmanipulation', ['action_type', 'value_1', 'value_2', 'buid', 'view_source', 'action'])


        # Changing field 'Redirect.uid'
        db.alter_column(u'redirect_redirect', 'uid', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True))

        # Changing field 'Redirect.company_name'
        db.alter_column(u'redirect_redirect', 'company_name', self.gf('django.db.models.fields.TextField')())
        # Adding field 'ViewSource.friendly_name'
        db.add_column(u'redirect_viewsource', 'friendly_name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)


        # Changing field 'DestinationManipulation.value_1'
        db.alter_column(u'redirect_destinationmanipulation', 'value_1', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'DestinationManipulation.value_2'
        db.alter_column(u'redirect_destinationmanipulation', 'value_2', self.gf('django.db.models.fields.TextField')(default=''))
        # Adding unique constraint on 'DestinationManipulation', fields ['buid', 'view_source', 'action_type']
        db.create_unique(u'redirect_destinationmanipulation', ['buid', 'view_source', 'action_type'])


    def backwards(self, orm):
        # Removing unique constraint on 'DestinationManipulation', fields ['buid', 'view_source', 'action_type']
        db.delete_unique(u'redirect_destinationmanipulation', ['buid', 'view_source', 'action_type'])


        # User chose to not deal with backwards NULL issues for 'Redirect.uid'
        raise RuntimeError("Cannot reverse this migration. 'Redirect.uid' and its values cannot be restored.")

        # Changing field 'Redirect.company_name'
        db.alter_column(u'redirect_redirect', 'company_name', self.gf('django.db.models.fields.CharField')(max_length=255))
        # Deleting field 'ViewSource.friendly_name'
        db.delete_column(u'redirect_viewsource', 'friendly_name')


        # Changing field 'DestinationManipulation.value_1'
        db.alter_column(u'redirect_destinationmanipulation', 'value_1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'DestinationManipulation.value_2'
        db.alter_column(u'redirect_destinationmanipulation', 'value_2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))
        # Adding unique constraint on 'DestinationManipulation', fields ['action_type', 'value_1', 'value_2', 'buid', 'view_source', 'action']
        db.create_unique(u'redirect_destinationmanipulation', ['action_type', 'value_1', 'value_2', 'buid', 'view_source', 'action'])


    models = {
        u'redirect.atssourcecode': {
            'Meta': {'unique_together': "(('ats_name', 'parameter_name', 'parameter_value', 'buid', 'view_source'),)", 'object_name': 'ATSSourceCode'},
            'ats_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parameter_value': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'view_source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.ViewSource']", 'null': 'True'})
        },
        u'redirect.canonicalmicrosite': {
            'Meta': {'object_name': 'CanonicalMicrosite'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0', 'primary_key': 'True'}),
            'canonical_microsite_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'redirect.destinationmanipulation': {
            'Meta': {'unique_together': "(('action_type', 'buid', 'view_source'),)", 'object_name': 'DestinationManipulation'},
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'action_type': ('django.db.models.fields.IntegerField', [], {}),
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_1': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'value_2': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {})
        },
        u'redirect.redirect': {
            'Meta': {'object_name': 'Redirect'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'company_name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expired_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'job_location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'new_date': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'default': '0', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'redirect.redirectaction': {
            'Meta': {'unique_together': "(('buid', 'view_source', 'action'),)", 'object_name': 'RedirectAction'},
            'action': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.ViewSource']"})
        },
        u'redirect.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'microsite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'view_source_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'primary_key': 'True'})
        }
    }

    complete_apps = ['redirect']