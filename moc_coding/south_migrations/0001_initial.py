# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Onet'
        db.create_table(u'moc_coding_onet', (
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10, primary_key=True)),
        ))
        db.send_create_signal(u'moc_coding', ['Onet'])

        # Adding unique constraint on 'Onet', fields ['title', 'code']
        db.create_unique(u'moc_coding_onet', ['title', 'code'])

        # Adding model 'Moc'
        db.create_table(u'moc_coding_moc', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=11)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('title_slug', self.gf('django.db.models.fields.SlugField')(max_length=300)),
            ('moc_detail', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['moc_coding.MocDetail'], unique=True, null=True)),
        ))
        db.send_create_signal(u'moc_coding', ['Moc'])

        # Adding unique constraint on 'Moc', fields ['code', 'branch']
        db.create_unique(u'moc_coding_moc', ['code', 'branch'])

        # Adding M2M table for field onets on 'Moc'
        m2m_table_name = db.shorten_name(u'moc_coding_moc_onets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('moc', models.ForeignKey(orm[u'moc_coding.moc'], null=False)),
            ('onet', models.ForeignKey(orm[u'moc_coding.onet'], null=False))
        ))
        db.create_unique(m2m_table_name, ['moc_id', 'onet_id'])

        # Adding model 'MocDetail'
        db.create_table(u'moc_coding_mocdetail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('primary_value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('service_branch', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('military_description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('civilian_description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'moc_coding', ['MocDetail'])

        # Adding model 'CustomCareer'
        db.create_table(u'moc_coding_customcareer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('moc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['moc_coding.Moc'])),
            ('onet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['moc_coding.Onet'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'moc_coding', ['CustomCareer'])


    def backwards(self, orm):
        # Removing unique constraint on 'Moc', fields ['code', 'branch']
        db.delete_unique(u'moc_coding_moc', ['code', 'branch'])

        # Removing unique constraint on 'Onet', fields ['title', 'code']
        db.delete_unique(u'moc_coding_onet', ['title', 'code'])

        # Deleting model 'Onet'
        db.delete_table(u'moc_coding_onet')

        # Deleting model 'Moc'
        db.delete_table(u'moc_coding_moc')

        # Removing M2M table for field onets on 'Moc'
        db.delete_table(db.shorten_name(u'moc_coding_moc_onets'))

        # Deleting model 'MocDetail'
        db.delete_table(u'moc_coding_mocdetail')

        # Deleting model 'CustomCareer'
        db.delete_table(u'moc_coding_customcareer')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'moc_coding.customcareer': {
            'Meta': {'object_name': 'CustomCareer'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['moc_coding.Moc']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'onet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['moc_coding.Onet']"})
        },
        u'moc_coding.moc': {
            'Meta': {'ordering': "['branch', 'code']", 'unique_together': "(('code', 'branch'),)", 'object_name': 'Moc'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '11'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moc_detail': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['moc_coding.MocDetail']", 'unique': 'True', 'null': 'True'}),
            'onets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['moc_coding.Onet']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'title_slug': ('django.db.models.fields.SlugField', [], {'max_length': '300'})
        },
        u'moc_coding.mocdetail': {
            'Meta': {'object_name': 'MocDetail'},
            'civilian_description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'military_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'primary_value': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'service_branch': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'moc_coding.onet': {
            'Meta': {'unique_together': "(('title', 'code'),)", 'object_name': 'Onet'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        }
    }

    complete_apps = ['moc_coding']