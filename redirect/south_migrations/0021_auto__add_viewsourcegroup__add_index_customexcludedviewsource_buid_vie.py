# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ViewSourceGroup'
        db.create_table(u'redirect_viewsourcegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'redirect', ['ViewSourceGroup'])

        # Adding M2M table for field view_source on 'ViewSourceGroup'
        m2m_table_name = db.shorten_name(u'redirect_viewsourcegroup_view_source')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('viewsourcegroup', models.ForeignKey(orm[u'redirect.viewsourcegroup'], null=False)),
            ('viewsource', models.ForeignKey(orm[u'redirect.viewsource'], null=False))
        ))
        db.create_unique(m2m_table_name, ['viewsourcegroup_id', 'viewsource_id'])

        # Adding index on 'CustomExcludedViewSource', fields ['buid', 'view_source']
        db.create_index(u'redirect_customexcludedviewsource', ['buid', 'view_source'])

        # Adding field 'ViewSource.include_ga_params'
        db.add_column(u'redirect_viewsource', 'include_ga_params',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding index on 'RedirectAction', fields ['buid', 'view_source']
        db.create_index(u'redirect_redirectaction', ['buid', 'view_source_id'])


    def backwards(self, orm):
        # Removing index on 'RedirectAction', fields ['buid', 'view_source']
        db.delete_index(u'redirect_redirectaction', ['buid', 'view_source_id'])

        # Removing index on 'CustomExcludedViewSource', fields ['buid', 'view_source']
        db.delete_index(u'redirect_customexcludedviewsource', ['buid', 'view_source'])

        # Deleting model 'ViewSourceGroup'
        db.delete_table(u'redirect_viewsourcegroup')

        # Removing M2M table for field view_source on 'ViewSourceGroup'
        db.delete_table(db.shorten_name(u'redirect_viewsourcegroup_view_source'))

        # Deleting field 'ViewSource.include_ga_params'
        db.delete_column(u'redirect_viewsource', 'include_ga_params')


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