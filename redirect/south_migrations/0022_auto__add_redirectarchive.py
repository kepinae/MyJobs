# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RedirectArchive'
        db_backend = settings.DATABASES['default']['ENGINE'].split('.')[-1]
        if db_backend == 'mysql':
            # The 'else' statement is the command that should've been used to
            # create the archive table. Unfortunately, there are some
            # alterations that were made and not recorded. To ensure that we
            # capture those alterations in the new table, make a copy
            # of the table instead.
            db.execute("CREATE TABLE redirect_redirectarchive LIKE redirect_redirect")

            # Adding index on 'Redirect', fields ['expired_date']
            db.create_index(u'redirect_redirectarchive', ['expired_date'])
        else:
            db.create_table(u'redirect_redirectarchive', (
                ('guid', self.gf('django.db.models.fields.CharField')(max_length=42, primary_key=True, db_index=True)),
                ('buid', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('uid', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True, blank=True)),
                ('url', self.gf('django.db.models.fields.TextField')()),
                ('new_date', self.gf('django.db.models.fields.DateTimeField')()),
                ('expired_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
                ('job_location', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
                ('job_title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
                ('company_name', self.gf('django.db.models.fields.TextField')(blank=True)),
            ))
            db.send_create_signal(u'redirect', ['RedirectArchive'])


    def backwards(self, orm):
        # Deleting model 'RedirectArchive'
        db.delete_table(u'redirect_redirectarchive')


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
        u'redirect.companyemail': {
            'Meta': {'object_name': 'CompanyEmail'},
            'buid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'})
        },
        u'redirect.customexcludedviewsource': {
            'Meta': {'unique_together': "(('buid', 'view_source'),)", 'object_name': 'CustomExcludedViewSource', 'index_together': "[['buid', 'view_source']]"},
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {})
        },
        u'redirect.destinationmanipulation': {
            'Meta': {'unique_together': "(('action_type', 'buid', 'view_source'),)", 'object_name': 'DestinationManipulation'},
            'action': ('django.db.models.fields.CharField', [], {'default': "'sourcecodetag'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'action_type': ('django.db.models.fields.IntegerField', [], {}),
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_1': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'value_2': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {})
        },
        u'redirect.emailredirectlog': {
            'Meta': {'object_name': 'EmailRedirectLog'},
            'buid': ('django.db.models.fields.IntegerField', [], {}),
            'from_addr': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'to_addr': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'to_guid': ('django.db.models.fields.CharField', [], {'max_length': '38'})
        },
        u'redirect.excludedviewsource': {
            'Meta': {'object_name': 'ExcludedViewSource'},
            'view_source': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        u'redirect.redirect': {
            'Meta': {'object_name': 'Redirect'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'company_name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expired_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'primary_key': 'True'}),
            'job_location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'new_date': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'redirect.redirectaction': {
            'Meta': {'unique_together': "(('buid', 'view_source', 'action'),)", 'object_name': 'RedirectAction', 'index_together': "[['buid', 'view_source']]"},
            'action': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['redirect.ViewSource']"})
        },
        u'redirect.redirectarchive': {
            'Meta': {'object_name': 'RedirectArchive'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'company_name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expired_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '42', 'primary_key': 'True', 'db_index': 'True'}),
            'job_location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'new_date': ('django.db.models.fields.DateTimeField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'redirect.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'include_ga_params': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'microsite': ('django.db.models.fields.BooleanField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'view_source_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'primary_key': 'True'})
        },
        u'redirect.viewsourcegroup': {
            'Meta': {'object_name': 'ViewSourceGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'view_source': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['redirect.ViewSource']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['redirect']