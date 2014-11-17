# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Block'
        db.create_table(u'myblocks_block', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('offset', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('span', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('template', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'myblocks', ['Block'])

        # Adding model 'ColumnBlock'
        db.create_table(u'myblocks_columnblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['ColumnBlock'])

        # Adding model 'ContentBlock'
        db.create_table(u'myblocks_contentblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['ContentBlock'])

        # Adding model 'ImageBlock'
        db.create_table(u'myblocks_imageblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
            ('image_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'myblocks', ['ImageBlock'])

        # Adding model 'LoginBlock'
        db.create_table(u'myblocks_loginblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['LoginBlock'])

        # Adding model 'RegistrationBlock'
        db.create_table(u'myblocks_registrationblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['RegistrationBlock'])

        # Adding model 'SavedSearchWidgetBlock'
        db.create_table(u'myblocks_savedsearchwidgetblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['SavedSearchWidgetBlock'])

        # Adding model 'SearchBoxBlock'
        db.create_table(u'myblocks_searchboxblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['SearchBoxBlock'])

        # Adding model 'SearchFilterBlock'
        db.create_table(u'myblocks_searchfilterblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['SearchFilterBlock'])

        # Adding model 'VeteranSearchBox'
        db.create_table(u'myblocks_veteransearchbox', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['VeteranSearchBox'])

        # Adding model 'SearchResultBlock'
        db.create_table(u'myblocks_searchresultblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['SearchResultBlock'])

        # Adding model 'ShareBlock'
        db.create_table(u'myblocks_shareblock', (
            (u'block_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['myblocks.Block'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'myblocks', ['ShareBlock'])

        # Adding model 'Row'
        db.create_table(u'myblocks_row', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'myblocks', ['Row'])

        # Adding model 'Page'
        db.create_table(u'myblocks_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bootstrap_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('page_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seo.SeoSite'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='production', max_length=255)),
        ))
        db.send_create_signal(u'myblocks', ['Page'])

        # Adding model 'BlockOrder'
        db.create_table(u'myblocks_blockorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('block', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myblocks.Block'])),
            ('row', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myblocks.Row'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'myblocks', ['BlockOrder'])

        # Adding model 'ColumnBlockOrder'
        db.create_table(u'myblocks_columnblockorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('block', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myblocks.Block'])),
            ('column_block', self.gf('django.db.models.fields.related.ForeignKey')(related_name='included_column_blocks', to=orm['myblocks.ColumnBlock'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'myblocks', ['ColumnBlockOrder'])

        # Adding model 'RowOrder'
        db.create_table(u'myblocks_roworder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('row', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myblocks.Row'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['myblocks.Page'])),
        ))
        db.send_create_signal(u'myblocks', ['RowOrder'])


    def backwards(self, orm):
        # Deleting model 'Block'
        db.delete_table(u'myblocks_block')

        # Deleting model 'ColumnBlock'
        db.delete_table(u'myblocks_columnblock')

        # Deleting model 'ContentBlock'
        db.delete_table(u'myblocks_contentblock')

        # Deleting model 'ImageBlock'
        db.delete_table(u'myblocks_imageblock')

        # Deleting model 'LoginBlock'
        db.delete_table(u'myblocks_loginblock')

        # Deleting model 'RegistrationBlock'
        db.delete_table(u'myblocks_registrationblock')

        # Deleting model 'SavedSearchWidgetBlock'
        db.delete_table(u'myblocks_savedsearchwidgetblock')

        # Deleting model 'SearchBoxBlock'
        db.delete_table(u'myblocks_searchboxblock')

        # Deleting model 'SearchFilterBlock'
        db.delete_table(u'myblocks_searchfilterblock')

        # Deleting model 'VeteranSearchBox'
        db.delete_table(u'myblocks_veteransearchbox')

        # Deleting model 'SearchResultBlock'
        db.delete_table(u'myblocks_searchresultblock')

        # Deleting model 'ShareBlock'
        db.delete_table(u'myblocks_shareblock')

        # Deleting model 'Row'
        db.delete_table(u'myblocks_row')

        # Deleting model 'Page'
        db.delete_table(u'myblocks_page')

        # Deleting model 'BlockOrder'
        db.delete_table(u'myblocks_blockorder')

        # Deleting model 'ColumnBlockOrder'
        db.delete_table(u'myblocks_columnblockorder')

        # Deleting model 'RowOrder'
        db.delete_table(u'myblocks_roworder')


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
        u'myblocks.block': {
            'Meta': {'object_name': 'Block'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'offset': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'span': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'template': ('django.db.models.fields.TextField', [], {})
        },
        u'myblocks.blockorder': {
            'Meta': {'ordering': "('order',)", 'object_name': 'BlockOrder'},
            'block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myblocks.Block']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'row': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myblocks.Row']"})
        },
        u'myblocks.columnblock': {
            'Meta': {'object_name': 'ColumnBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'}),
            'blocks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'included_blocks'", 'symmetrical': 'False', 'through': u"orm['myblocks.ColumnBlockOrder']", 'to': u"orm['myblocks.Block']"})
        },
        u'myblocks.columnblockorder': {
            'Meta': {'ordering': "('order',)", 'object_name': 'ColumnBlockOrder'},
            'block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myblocks.Block']"}),
            'column_block': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'included_column_blocks'", 'to': u"orm['myblocks.ColumnBlock']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'myblocks.contentblock': {
            'Meta': {'object_name': 'ContentBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.imageblock': {
            'Meta': {'object_name': 'ImageBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'myblocks.loginblock': {
            'Meta': {'object_name': 'LoginBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.page': {
            'Meta': {'object_name': 'Page'},
            'bootstrap_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'rows': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['myblocks.Row']", 'through': u"orm['myblocks.RowOrder']", 'symmetrical': 'False'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.SeoSite']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'production'", 'max_length': '255'})
        },
        u'myblocks.registrationblock': {
            'Meta': {'object_name': 'RegistrationBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.row': {
            'Meta': {'object_name': 'Row'},
            'blocks': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['myblocks.Block']", 'through': u"orm['myblocks.BlockOrder']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'template': ('django.db.models.fields.TextField', [], {})
        },
        u'myblocks.roworder': {
            'Meta': {'ordering': "('order',)", 'object_name': 'RowOrder'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myblocks.Page']"}),
            'row': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myblocks.Row']"})
        },
        u'myblocks.savedsearchwidgetblock': {
            'Meta': {'object_name': 'SavedSearchWidgetBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.searchboxblock': {
            'Meta': {'object_name': 'SearchBoxBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.searchfilterblock': {
            'Meta': {'object_name': 'SearchFilterBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.searchresultblock': {
            'Meta': {'object_name': 'SearchResultBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.shareblock': {
            'Meta': {'object_name': 'ShareBlock', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'myblocks.veteransearchbox': {
            'Meta': {'object_name': 'VeteranSearchBox', '_ormbases': [u'myblocks.Block']},
            u'block_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['myblocks.Block']", 'unique': 'True', 'primary_key': 'True'})
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
        u'postajob.package': {
            'Meta': {'object_name': 'Package'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'postajob.sitepackage': {
            'Meta': {'object_name': 'SitePackage', '_ormbases': [u'postajob.Package']},
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Company']", 'null': 'True', 'blank': 'True'}),
            u'package_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['postajob.Package']", 'unique': 'True', 'primary_key': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.SeoSite']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'seo.atssourcecode': {
            'Meta': {'object_name': 'ATSSourceCode'},
            'ats_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        },
        u'seo.billboardimage': {
            'Meta': {'object_name': 'BillboardImage'},
            'copyright_info': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'sponsor_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'seo.businessunit': {
            'Meta': {'object_name': 'BusinessUnit'},
            'associated_jobs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_crawled': ('django.db.models.fields.DateTimeField', [], {}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'enable_markdown': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'federal_contractor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'max_length': '10', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'title_slug': ('django.db.models.fields.SlugField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        u'seo.company': {
            'Meta': {'ordering': "['name']", 'object_name': 'Company'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['myjobs.User']", 'through': u"orm['seo.CompanyUser']", 'symmetrical': 'False'}),
            'canonical_microsite': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'company_slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'digital_strategies_customer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enhanced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_source_ids': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.BusinessUnit']", 'symmetrical': 'False'}),
            'linkedin_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'logo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'member': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'og_img': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'prm_access': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'product_access': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site_package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['postajob.SitePackage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'seo.companyuser': {
            'Meta': {'unique_together': "(('user', 'company'),)", 'object_name': 'CompanyUser', 'db_table': "'mydashboard_companyuser'"},
            'company': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.Company']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['myjobs.User']"})
        },
        u'seo.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'backgroundColor': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'browse_city_order': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'browse_city_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_city_text': ('django.db.models.fields.CharField', [], {'default': "'City'", 'max_length': '50'}),
            'browse_company_order': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'browse_company_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_company_text': ('django.db.models.fields.CharField', [], {'default': "'Company'", 'max_length': '50'}),
            'browse_country_order': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'browse_country_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_country_text': ('django.db.models.fields.CharField', [], {'default': "'Country'", 'max_length': '50'}),
            'browse_facet_order': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'browse_facet_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_facet_text': ('django.db.models.fields.CharField', [], {'default': "'Job Profiles'", 'max_length': '50'}),
            'browse_moc_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'browse_moc_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'browse_moc_text': ('django.db.models.fields.CharField', [], {'default': "'Military Titles'", 'max_length': '50'}),
            'browse_state_order': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'browse_state_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_state_text': ('django.db.models.fields.CharField', [], {'default': "'State'", 'max_length': '50'}),
            'browse_title_order': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'browse_title_show': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'browse_title_text': ('django.db.models.fields.CharField', [], {'default': "'Title'", 'max_length': '50'}),
            'company_tag': ('django.db.models.fields.CharField', [], {'default': "'careers'", 'max_length': '50'}),
            'defaultBlurb': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'defaultBlurbTitle': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'directemployers_link': ('django.db.models.fields.URLField', [], {'default': "'http://directemployers.org'", 'max_length': '200'}),
            'facet_tag': ('django.db.models.fields.CharField', [], {'default': "'new-jobs'", 'max_length': '50'}),
            'fontColor': ('django.db.models.fields.CharField', [], {'default': "'666666'", 'max_length': '6'}),
            'footer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            'header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'home_page_template': ('django.db.models.fields.CharField', [], {'default': "'home_page/home_page_listing.html'", 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_tag': ('django.db.models.fields.CharField', [], {'default': "'jobs'", 'max_length': '50'}),
            'meta': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'moc_tag': ('django.db.models.fields.CharField', [], {'default': "'vet-jobs'", 'max_length': '50'}),
            'num_filter_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'num_job_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'num_subnav_items_to_show': ('django.db.models.fields.IntegerField', [], {'default': '9'}),
            'percent_featured': ('django.db.models.fields.DecimalField', [], {'default': "'0.5'", 'max_digits': '3', 'decimal_places': '2'}),
            'primaryColor': ('django.db.models.fields.CharField', [], {'default': "'990000'", 'max_length': '6'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'show_home_microsite_carousel': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_home_social_footer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_saved_search_widget': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_social_footer': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title_tag': ('django.db.models.fields.CharField', [], {'default': "'jobs-in'", 'max_length': '50'}),
            'view_all_jobs_detail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wide_footer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'wide_header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'seo.customfacet': {
            'Meta': {'object_name': 'CustomFacet'},
            'always_show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blurb': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'business_units': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BusinessUnit']", 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'onet': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'querystring': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'saved_querystring': ('django.db.models.fields.CharField', [], {'max_length': '10000', 'blank': 'True'}),
            'show_blurb': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_production': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '800', 'null': 'True', 'blank': 'True'}),
            'url_slab': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'seo.googleanalytics': {
            'Meta': {'object_name': 'GoogleAnalytics'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'web_property_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'seo.googleanalyticscampaign': {
            'Meta': {'object_name': 'GoogleAnalyticsCampaign'},
            'campaign_content': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_medium': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'campaign_term': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        },
        u'seo.seosite': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'SeoSite', '_ormbases': [u'sites.Site']},
            'ats_source_codes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.ATSSourceCode']", 'null': 'True', 'blank': 'True'}),
            'billboard_images': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BillboardImage']", 'null': 'True', 'blank': 'True'}),
            'business_units': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.BusinessUnit']", 'null': 'True', 'blank': 'True'}),
            'configurations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['seo.Configuration']", 'symmetrical': 'False', 'blank': 'True'}),
            'facets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.CustomFacet']", 'null': 'True', 'through': u"orm['seo.SeoSiteFacet']", 'blank': 'True'}),
            'featured_companies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.Company']", 'null': 'True', 'blank': 'True'}),
            'google_analytics': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.GoogleAnalytics']", 'null': 'True', 'blank': 'True'}),
            'google_analytics_campaigns': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.GoogleAnalyticsCampaign']", 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            'microsite_carousel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social_links.MicrositeCarousel']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'postajob_filter_type': ('django.db.models.fields.CharField', [], {'default': "'this site only'", 'max_length': '255', 'blank': 'True'}),
            'site_description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'site_heading': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'site_package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['postajob.SitePackage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            u'site_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sites.Site']", 'unique': 'True', 'primary_key': 'True'}),
            'site_tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.SiteTag']", 'null': 'True', 'blank': 'True'}),
            'site_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'special_commitments': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seo.SpecialCommitment']", 'null': 'True', 'blank': 'True'}),
            'view_sources': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.ViewSource']", 'null': 'True', 'blank': 'True'})
        },
        u'seo.seositefacet': {
            'Meta': {'object_name': 'SeoSiteFacet'},
            'boolean_operation': ('django.db.models.fields.CharField', [], {'default': "'or'", 'max_length': '3', 'db_index': 'True'}),
            'customfacet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.CustomFacet']"}),
            'facet_type': ('django.db.models.fields.CharField', [], {'default': "'STD'", 'max_length': '4', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seosite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seo.SeoSite']"})
        },
        u'seo.sitetag': {
            'Meta': {'object_name': 'SiteTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site_tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'tag_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'seo.specialcommitment': {
            'Meta': {'object_name': 'SpecialCommitment'},
            'commit': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'seo.viewsource': {
            'Meta': {'object_name': 'ViewSource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'view_source': ('django.db.models.fields.IntegerField', [], {'default': "''", 'max_length': '20'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'social_links.micrositecarousel': {
            'Meta': {'object_name': 'MicrositeCarousel'},
            'carousel_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'display_rows': ('django.db.models.fields.IntegerField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_all_sites': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'link_sites': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'linked_carousel'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['seo.SeoSite']"})
        }
    }

    complete_apps = ['myblocks']