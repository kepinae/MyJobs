# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Redirect'
        db.create_table(u'redirect_redirect', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('canonical_microsite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['redirect.CanonicalMicrosite'])),
            ('uid', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('new_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('expired_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'redirect', ['Redirect'])

        # Adding model 'ATSSourceCode'
        db.create_table(u'redirect_atssourcecode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ats_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('parameter_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('parameter_value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'redirect', ['ATSSourceCode'])

        # Adding model 'CanonicalMicrosite'
        db.create_table(u'redirect_canonicalmicrosite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('buid', self.gf('django.db.models.fields.IntegerField')()),
            ('canonical_microsite_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'redirect', ['CanonicalMicrosite'])

        # Adding model 'RedirectAction'
        db.create_table(u'redirect_redirectaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('canonical_microsite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['redirect.CanonicalMicrosite'])),
            ('view_source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['redirect.ViewSource'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'redirect', ['RedirectAction'])

        # Adding model 'ViewSource'
        db.create_table(u'redirect_viewsource', (
            ('viewsource_id', self.gf('django.db.models.fields.IntegerField')(default=0, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('microsite', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'redirect', ['ViewSource'])


    def backwards(self, orm):
        # Deleting model 'Redirect'
        db.delete_table(u'redirect_redirect')

        # Deleting model 'ATSSourceCode'
        db.delete_table(u'redirect_atssourcecode')

        # Deleting model 'CanonicalMicrosite'
        db.delete_table(u'redirect_canonicalmicrosite')

        # Deleting model 'RedirectAction'
        db.delete_table(u'redirect_redirectaction')

        # Deleting model 'ViewSource'
        db.delete_table(u'redirect_viewsource')


    models = {
        u'redirect.atssourcecode': {
            'Meta': {'object_name': 'ATSSourceCode'},
            'ats_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parameter_value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'redirect.canonicalmicrosite': {
            'Meta': {'object_name': 'CanonicalMicrosite'},
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            'canonical_microsite_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'redirect.redirect': {
            'Meta': {'object_name': 'Redirect'},
            'canonical_microsite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.CanonicalMicrosite']"}),
            'expired_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_date': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'redirect.redirectaction': {
            'Meta': {'object_name': 'RedirectAction'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'canonical_microsite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.CanonicalMicrosite']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.ViewSource']"})
        },
        u'redirect.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            'microsite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'viewsource_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'primary_key': 'True'})
        }
    }

    complete_apps = ['redirect']