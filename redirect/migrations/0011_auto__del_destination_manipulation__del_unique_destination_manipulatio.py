# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Destination_Manipulation', fields ['ActionType', 'BUID', 'ViewSourceID', 'Action', 'Value1', 'Value2']
        db.delete_unique(u'redirect_destination_manipulation', ['ActionType', 'BUID', 'ViewSourceID', 'Action', 'Value1', 'Value2'])

        # Deleting model 'Destination_Manipulation'
        db.delete_table(u'redirect_destination_manipulation')

        # Adding model 'DestinationManipulation'
        db.create_table(u'redirect_destinationmanipulation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_type', self.gf('django.db.models.fields.IntegerField')()),
            ('buid', self.gf('django.db.models.fields.IntegerField')()),
            ('view_source', self.gf('django.db.models.fields.IntegerField')()),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value_1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value_2', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'redirect', ['DestinationManipulation'])

        # Adding unique constraint on 'DestinationManipulation', fields ['action_type', 'buid', 'view_source', 'action', 'value_1', 'value_2']
        db.create_unique(u'redirect_destinationmanipulation', ['action_type', 'buid', 'view_source', 'action', 'value_1', 'value_2'])


    def backwards(self, orm):
        # Removing unique constraint on 'DestinationManipulation', fields ['action_type', 'buid', 'view_source', 'action', 'value_1', 'value_2']
        db.delete_unique(u'redirect_destinationmanipulation', ['action_type', 'buid', 'view_source', 'action', 'value_1', 'value_2'])

        # Adding model 'Destination_Manipulation'
        db.create_table(u'redirect_destination_manipulation', (
            ('BUID', self.gf('django.db.models.fields.IntegerField')()),
            ('ActionType', self.gf('django.db.models.fields.IntegerField')()),
            ('Value2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('Value1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ViewSourceID', self.gf('django.db.models.fields.IntegerField')()),
            ('Action', self.gf('django.db.models.fields.CharField')(max_length=255)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'redirect', ['Destination_Manipulation'])

        # Adding unique constraint on 'Destination_Manipulation', fields ['ActionType', 'BUID', 'ViewSourceID', 'Action', 'Value1', 'Value2']
        db.create_unique(u'redirect_destination_manipulation', ['ActionType', 'BUID', 'ViewSourceID', 'Action', 'Value1', 'Value2'])

        # Deleting model 'DestinationManipulation'
        db.delete_table(u'redirect_destinationmanipulation')


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
            'Meta': {'unique_together': "(('action_type', 'buid', 'view_source', 'action', 'value_1', 'value_2'),)", 'object_name': 'DestinationManipulation'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'action_type': ('django.db.models.fields.IntegerField', [], {}),
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value_2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {})
        },
        u'redirect.redirect': {
            'Meta': {'object_name': 'Redirect'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'expired_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'job_location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'new_date': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
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
            'microsite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'view_source_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'primary_key': 'True'})
        }
    }

    complete_apps = ['redirect']