# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'ATSSourceCode', fields ['buid', 'parameter_value', 'ats_name', 'view_source', 'parameter_name']
        db.delete_unique(u'redirect_atssourcecode', ['buid', 'parameter_value', 'ats_name', 'view_source_id', 'parameter_name'])

        # Adding unique constraint on 'ATSSourceCode', fields ['parameter_value', 'ats_name', 'parameter_name']
        db.create_unique(u'redirect_atssourcecode', ['parameter_value', 'ats_name', 'parameter_name'])

        # Adding unique constraint on 'ATSSourceCode', fields ['buid', 'view_source']
        db.create_unique(u'redirect_atssourcecode', ['buid', 'view_source_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ATSSourceCode', fields ['buid', 'view_source']
        db.delete_unique(u'redirect_atssourcecode', ['buid', 'view_source_id'])

        # Removing unique constraint on 'ATSSourceCode', fields ['parameter_value', 'ats_name', 'parameter_name']
        db.delete_unique(u'redirect_atssourcecode', ['parameter_value', 'ats_name', 'parameter_name'])

        # Adding unique constraint on 'ATSSourceCode', fields ['buid', 'parameter_value', 'ats_name', 'view_source', 'parameter_name']
        db.create_unique(u'redirect_atssourcecode', ['buid', 'parameter_value', 'ats_name', 'view_source_id', 'parameter_name'])


    models = {
        u'redirect.atssourcecode': {
            'Meta': {'unique_together': "(('ats_name', 'parameter_name', 'parameter_value'), ('buid', 'view_source'))", 'object_name': 'ATSSourceCode'},
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
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'redirect.redirectaction': {
            'Meta': {'unique_together': "(('buid', 'view_source', 'action'),)", 'object_name': 'RedirectAction'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.ViewSource']"})
        },
        u'redirect.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            'microsite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'view_source_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'primary_key': 'True'})
        }
    }

    complete_apps = ['redirect']