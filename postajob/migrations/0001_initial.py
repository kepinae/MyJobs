# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(max_length=255, verbose_name=b'Company Description', blank=True)),
                ('address_line_one', models.CharField(max_length=255, verbose_name=b'Address Line One', blank=True)),
                ('address_line_two', models.CharField(max_length=255, verbose_name=b'Address Line Two', blank=True)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('state', models.CharField(max_length=255, blank=True)),
                ('country', models.CharField(default=b'United States', max_length=255, choices=[(b'Afghanistan', b'Afghanistan'), (b'Albania', b'Albania'), (b'Algeria', b'Algeria'), (b'American Samoa', b'American Samoa'), (b'Andorra', b'Andorra'), (b'Angola', b'Angola'), (b'Anguilla', b'Anguilla'), (b'Antartica', b'Antartica'), (b'Antigua and Barbuda', b'Antigua and Barbuda'), (b'Argentina', b'Argentina'), (b'Armenia', b'Armenia'), (b'Aruba', b'Aruba'), (b'Australia', b'Australia'), (b'Austria', b'Austria'), (b'Azerbaijan', b'Azerbaijan'), (b'Bahamas', b'Bahamas'), (b'Bahrain', b'Bahrain'), (b'Bangladesh', b'Bangladesh'), (b'Barbados', b'Barbados'), (b'Belarus', b'Belarus'), (b'Belgium', b'Belgium'), (b'Belize', b'Belize'), (b'Benin', b'Benin'), (b'Bermuda', b'Bermuda'), (b'Bhutan', b'Bhutan'), (b'Bolivia', b'Bolivia'), (b'Bosnia', b'Bosnia'), (b'Botswana', b'Botswana'), (b'Brazil', b'Brazil'), (b'Brunei Darussalam', b'Brunei Darussalam'), (b'Bulgaria', b'Bulgaria'), (b'Burkina Faso', b'Burkina Faso'), (b'Burundi', b'Burundi'), (b'Cambodia', b'Cambodia'), (b'Cameroon', b'Cameroon'), (b'Canada', b'Canada'), (b'Cape Verde', b'Cape Verde'), (b'Cayman Islands', b'Cayman Islands'), (b'Central African Republic', b'Central African Republic'), (b'Chad', b'Chad'), (b'Chile', b'Chile'), (b'China', b'China'), (b'Colombia', b'Colombia'), (b'Comoros', b'Comoros'), (b'Congo', b'Congo'), (b'Cook Islands', b'Cook Islands'), (b'Costa Rica', b'Costa Rica'), (b"Cote D'Ivoire", b"Cote D'Ivoire"), (b'Croatia', b'Croatia'), (b'Cuba', b'Cuba'), (b'Cyprus', b'Cyprus'), (b'Czech Republic', b'Czech Republic'), (b'Denmark', b'Denmark'), (b'Djibouti', b'Djibouti'), (b'Dominica', b'Dominica'), (b'Dominican Republic', b'Dominican Republic'), (b'East Timor', b'East Timor'), (b'Ecuador', b'Ecuador'), (b'Egypt', b'Egypt'), (b'El Salvador', b'El Salvador'), (b'Equatorial Guinea', b'Equatorial Guinea'), (b'Eritrea', b'Eritrea'), (b'Estonia', b'Estonia'), (b'Ethiopia', b'Ethiopia'), (b'Falkland Islands', b'Falkland Islands'), (b'Faroe Islands', b'Faroe Islands'), (b'Fiji', b'Fiji'), (b'Finland', b'Finland'), (b'France', b'France'), (b'French Guiana', b'French Guiana'), (b'French Polynesia', b'French Polynesia'), (b'Gabon', b'Gabon'), (b'Gambia', b'Gambia'), (b'Georgia', b'Georgia'), (b'Germany', b'Germany'), (b'Ghana', b'Ghana'), (b'Gibraltar', b'Gibraltar'), (b'Greece', b'Greece'), (b'Greenland', b'Greenland'), (b'Grenada', b'Grenada'), (b'Guadeloupe', b'Guadeloupe'), (b'Guatemala', b'Guatemala'), (b'Guinea', b'Guinea'), (b'Guinea-bissau', b'Guinea-bissau'), (b'Guyana', b'Guyana'), (b'Haiti', b'Haiti'), (b'Honduras', b'Honduras'), (b'Hong Kong', b'Hong Kong'), (b'Hungary', b'Hungary'), (b'Iceland', b'Iceland'), (b'India', b'India'), (b'Indonesia', b'Indonesia'), (b'Iran', b'Iran'), (b'Iraq', b'Iraq'), (b'Ireland', b'Ireland'), (b'Israel', b'Israel'), (b'Italy', b'Italy'), (b'Jamaica', b'Jamaica'), (b'Japan', b'Japan'), (b'Jordan', b'Jordan'), (b'Kazakhstan', b'Kazakhstan'), (b'Kenya', b'Kenya'), (b'Kuwait', b'Kuwait'), (b'Kyrgyzstan', b'Kyrgyzstan'), (b'Laos', b'Laos'), (b'Latvia', b'Latvia'), (b'Lebanon', b'Lebanon'), (b'Lesotho', b'Lesotho'), (b'Liberia', b'Liberia'), (b'Libyan Arab Jamahiriya', b'Libyan Arab Jamahiriya'), (b'Liechtenstein', b'Liechtenstein'), (b'Lithuania', b'Lithuania'), (b'Luxembourg ', b'Luxembourg '), (b'Macau', b'Macau'), (b'Macedonia', b'Macedonia'), (b'Madagascar', b'Madagascar'), (b'Malawi', b'Malawi'), (b'Malaysia', b'Malaysia'), (b'Maldives', b'Maldives'), (b'Mali', b'Mali'), (b'Malta', b'Malta'), (b'Marshall Islands', b'Marshall Islands'), (b'Martinique', b'Martinique'), (b'Mauritania', b'Mauritania'), (b'Mauritius', b'Mauritius'), (b'Mexico', b'Mexico'), (b'Micronesia', b'Micronesia'), (b'Moldova', b'Moldova'), (b'Monaco', b'Monaco'), (b'Mongolia', b'Mongolia'), (b'Montserrat', b'Montserrat'), (b'Morocco', b'Morocco'), (b'Mozambique', b'Mozambique'), (b'Multiple Asian Countries', b'Multiple Asian Countries'), (b'Multiple European Countries', b'Multiple European Countries'), (b'Myanmar', b'Myanmar'), (b'Namibia', b'Namibia'), (b'Nepal', b'Nepal'), (b'Netherlands', b'Netherlands'), (b'New Zealand', b'New Zealand'), (b'Nicaragua', b'Nicaragua'), (b'Niger', b'Niger'), (b'Nigeria', b'Nigeria'), (b'North Korea', b'North Korea'), (b'Northern Mariana Islands', b'Northern Mariana Islands'), (b'Norway', b'Norway'), (b'Oman', b'Oman'), (b'Pakistan', b'Pakistan'), (b'Palau', b'Palau'), (b'Palestine', b'Palestine'), (b'Panama', b'Panama'), (b'Papua New Guinea', b'Papua New Guinea'), (b'Paraguay', b'Paraguay'), (b'Peru', b'Peru'), (b'Philippines', b'Philippines'), (b'Poland', b'Poland'), (b'Portugal', b'Portugal'), (b'Qatar', b'Qatar'), (b'Reunion Island', b'Reunion Island'), (b'Romania', b'Romania'), (b'Russia', b'Russia'), (b'Rwanda', b'Rwanda'), (b'Saint Kitts and Nevis', b'Saint Kitts and Nevis'), (b'Samoa', b'Samoa'), (b'San Marino', b'San Marino'), (b'Sao Tome and Principe', b'Sao Tome and Principe'), (b'Saudi Arabia', b'Saudi Arabia'), (b'Senegal', b'Senegal'), (b'Serbia and Montenegro', b'Serbia and Montenegro'), (b'Seychelles', b'Seychelles'), (b'Sierra Leone', b'Sierra Leone'), (b'Singapore', b'Singapore'), (b'Slovak Republic', b'Slovak Republic'), (b'Slovenia', b'Slovenia'), (b'Somalia', b'Somalia'), (b'South Africa', b'South Africa'), (b'South Korea', b'South Korea'), (b'Spain', b'Spain'), (b'Sri Lanka', b'Sri Lanka'), (b'Sudan', b'Sudan'), (b'Suriname', b'Suriname'), (b'Swaziland', b'Swaziland'), (b'Sweden', b'Sweden'), (b'Switzerland', b'Switzerland'), (b'Syria', b'Syria'), (b'Taiwan', b'Taiwan'), (b'Tajikistan', b'Tajikistan'), (b'Tanzania', b'Tanzania'), (b'Thailand', b'Thailand'), (b'The Vatican', b'The Vatican'), (b'Togo', b'Togo'), (b'Trinidad and Tobago', b'Trinidad and Tobago'), (b'Tunisia', b'Tunisia'), (b'Turkey', b'Turkey'), (b'Turkmenistan', b'Turkmenistan'), (b'Turks and Caicos Islands', b'Turks and Caicos Islands'), (b'Tuvalu', b'Tuvalu'), (b'US Minor Outlying Islands', b'US Minor Outlying Islands'), (b'Uganda', b'Uganda'), (b'Ukraine', b'Ukraine'), (b'United Arab Emirates', b'United Arab Emirates'), (b'United Kingdom', b'United Kingdom'), (b'United States', b'United States'), (b'Uruguay', b'Uruguay'), (b'Uzbekistan', b'Uzbekistan'), (b'Venezuela', b'Venezuela'), (b'Vietnam', b'Vietnam'), (b'Virgin Islands (British)', b'Virgin Islands (British)'), (b'Virgin Islands (US)', b'Virgin Islands (US)'), (b'Western Sahara', b'Western Sahara'), (b'Yemen', b'Yemen'), (b'Yugoslavia', b'Yugoslavia'), (b'Zambia', b'Zambia'), (b'Zimbabwe', b'Zimbabwe')])),
                ('zipcode', models.CharField(max_length=255, blank=True)),
                ('phone', models.CharField(max_length=255, blank=True)),
                ('authorize_net_login', models.CharField(help_text=b"<a href='https://www.authorize.net' target='blank_'>Create Authorize.net account</a>", max_length=255, verbose_name=b'Authorize.net Login', blank=True)),
                ('authorize_net_transaction_key', models.CharField(max_length=255, verbose_name=b'Authorize.net Transaction Key', blank=True)),
                ('email_on_request', models.BooleanField(default=True, help_text=b'Send email to admins every time a request is made.')),
                ('outgoing_email_domain', models.CharField(default=b'my.jobs', max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('transaction_type', models.IntegerField(choices=[(1, b'Authorize.Net'), (2, b'Free'), (3, b'Offline Purchase')])),
                ('transaction', models.CharField(max_length=255, blank=True)),
                ('card_last_four', models.CharField(max_length=5, blank=True)),
                ('card_exp_date', models.DateField(null=True, blank=True)),
                ('first_name', models.CharField(max_length=255, verbose_name=b'First Name')),
                ('last_name', models.CharField(max_length=255, verbose_name=b'Last Name')),
                ('address_line_one', models.CharField(max_length=255, verbose_name=b'Address Line One')),
                ('address_line_two', models.CharField(max_length=255, verbose_name=b'Address Line Two', blank=True)),
                ('city', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
                ('country', models.CharField(default=b'United States', max_length=255, choices=[(b'Afghanistan', b'Afghanistan'), (b'Albania', b'Albania'), (b'Algeria', b'Algeria'), (b'American Samoa', b'American Samoa'), (b'Andorra', b'Andorra'), (b'Angola', b'Angola'), (b'Anguilla', b'Anguilla'), (b'Antartica', b'Antartica'), (b'Antigua and Barbuda', b'Antigua and Barbuda'), (b'Argentina', b'Argentina'), (b'Armenia', b'Armenia'), (b'Aruba', b'Aruba'), (b'Australia', b'Australia'), (b'Austria', b'Austria'), (b'Azerbaijan', b'Azerbaijan'), (b'Bahamas', b'Bahamas'), (b'Bahrain', b'Bahrain'), (b'Bangladesh', b'Bangladesh'), (b'Barbados', b'Barbados'), (b'Belarus', b'Belarus'), (b'Belgium', b'Belgium'), (b'Belize', b'Belize'), (b'Benin', b'Benin'), (b'Bermuda', b'Bermuda'), (b'Bhutan', b'Bhutan'), (b'Bolivia', b'Bolivia'), (b'Bosnia', b'Bosnia'), (b'Botswana', b'Botswana'), (b'Brazil', b'Brazil'), (b'Brunei Darussalam', b'Brunei Darussalam'), (b'Bulgaria', b'Bulgaria'), (b'Burkina Faso', b'Burkina Faso'), (b'Burundi', b'Burundi'), (b'Cambodia', b'Cambodia'), (b'Cameroon', b'Cameroon'), (b'Canada', b'Canada'), (b'Cape Verde', b'Cape Verde'), (b'Cayman Islands', b'Cayman Islands'), (b'Central African Republic', b'Central African Republic'), (b'Chad', b'Chad'), (b'Chile', b'Chile'), (b'China', b'China'), (b'Colombia', b'Colombia'), (b'Comoros', b'Comoros'), (b'Congo', b'Congo'), (b'Cook Islands', b'Cook Islands'), (b'Costa Rica', b'Costa Rica'), (b"Cote D'Ivoire", b"Cote D'Ivoire"), (b'Croatia', b'Croatia'), (b'Cuba', b'Cuba'), (b'Cyprus', b'Cyprus'), (b'Czech Republic', b'Czech Republic'), (b'Denmark', b'Denmark'), (b'Djibouti', b'Djibouti'), (b'Dominica', b'Dominica'), (b'Dominican Republic', b'Dominican Republic'), (b'East Timor', b'East Timor'), (b'Ecuador', b'Ecuador'), (b'Egypt', b'Egypt'), (b'El Salvador', b'El Salvador'), (b'Equatorial Guinea', b'Equatorial Guinea'), (b'Eritrea', b'Eritrea'), (b'Estonia', b'Estonia'), (b'Ethiopia', b'Ethiopia'), (b'Falkland Islands', b'Falkland Islands'), (b'Faroe Islands', b'Faroe Islands'), (b'Fiji', b'Fiji'), (b'Finland', b'Finland'), (b'France', b'France'), (b'French Guiana', b'French Guiana'), (b'French Polynesia', b'French Polynesia'), (b'Gabon', b'Gabon'), (b'Gambia', b'Gambia'), (b'Georgia', b'Georgia'), (b'Germany', b'Germany'), (b'Ghana', b'Ghana'), (b'Gibraltar', b'Gibraltar'), (b'Greece', b'Greece'), (b'Greenland', b'Greenland'), (b'Grenada', b'Grenada'), (b'Guadeloupe', b'Guadeloupe'), (b'Guatemala', b'Guatemala'), (b'Guinea', b'Guinea'), (b'Guinea-bissau', b'Guinea-bissau'), (b'Guyana', b'Guyana'), (b'Haiti', b'Haiti'), (b'Honduras', b'Honduras'), (b'Hong Kong', b'Hong Kong'), (b'Hungary', b'Hungary'), (b'Iceland', b'Iceland'), (b'India', b'India'), (b'Indonesia', b'Indonesia'), (b'Iran', b'Iran'), (b'Iraq', b'Iraq'), (b'Ireland', b'Ireland'), (b'Israel', b'Israel'), (b'Italy', b'Italy'), (b'Jamaica', b'Jamaica'), (b'Japan', b'Japan'), (b'Jordan', b'Jordan'), (b'Kazakhstan', b'Kazakhstan'), (b'Kenya', b'Kenya'), (b'Kuwait', b'Kuwait'), (b'Kyrgyzstan', b'Kyrgyzstan'), (b'Laos', b'Laos'), (b'Latvia', b'Latvia'), (b'Lebanon', b'Lebanon'), (b'Lesotho', b'Lesotho'), (b'Liberia', b'Liberia'), (b'Libyan Arab Jamahiriya', b'Libyan Arab Jamahiriya'), (b'Liechtenstein', b'Liechtenstein'), (b'Lithuania', b'Lithuania'), (b'Luxembourg ', b'Luxembourg '), (b'Macau', b'Macau'), (b'Macedonia', b'Macedonia'), (b'Madagascar', b'Madagascar'), (b'Malawi', b'Malawi'), (b'Malaysia', b'Malaysia'), (b'Maldives', b'Maldives'), (b'Mali', b'Mali'), (b'Malta', b'Malta'), (b'Marshall Islands', b'Marshall Islands'), (b'Martinique', b'Martinique'), (b'Mauritania', b'Mauritania'), (b'Mauritius', b'Mauritius'), (b'Mexico', b'Mexico'), (b'Micronesia', b'Micronesia'), (b'Moldova', b'Moldova'), (b'Monaco', b'Monaco'), (b'Mongolia', b'Mongolia'), (b'Montserrat', b'Montserrat'), (b'Morocco', b'Morocco'), (b'Mozambique', b'Mozambique'), (b'Multiple Asian Countries', b'Multiple Asian Countries'), (b'Multiple European Countries', b'Multiple European Countries'), (b'Myanmar', b'Myanmar'), (b'Namibia', b'Namibia'), (b'Nepal', b'Nepal'), (b'Netherlands', b'Netherlands'), (b'New Zealand', b'New Zealand'), (b'Nicaragua', b'Nicaragua'), (b'Niger', b'Niger'), (b'Nigeria', b'Nigeria'), (b'North Korea', b'North Korea'), (b'Northern Mariana Islands', b'Northern Mariana Islands'), (b'Norway', b'Norway'), (b'Oman', b'Oman'), (b'Pakistan', b'Pakistan'), (b'Palau', b'Palau'), (b'Palestine', b'Palestine'), (b'Panama', b'Panama'), (b'Papua New Guinea', b'Papua New Guinea'), (b'Paraguay', b'Paraguay'), (b'Peru', b'Peru'), (b'Philippines', b'Philippines'), (b'Poland', b'Poland'), (b'Portugal', b'Portugal'), (b'Qatar', b'Qatar'), (b'Reunion Island', b'Reunion Island'), (b'Romania', b'Romania'), (b'Russia', b'Russia'), (b'Rwanda', b'Rwanda'), (b'Saint Kitts and Nevis', b'Saint Kitts and Nevis'), (b'Samoa', b'Samoa'), (b'San Marino', b'San Marino'), (b'Sao Tome and Principe', b'Sao Tome and Principe'), (b'Saudi Arabia', b'Saudi Arabia'), (b'Senegal', b'Senegal'), (b'Serbia and Montenegro', b'Serbia and Montenegro'), (b'Seychelles', b'Seychelles'), (b'Sierra Leone', b'Sierra Leone'), (b'Singapore', b'Singapore'), (b'Slovak Republic', b'Slovak Republic'), (b'Slovenia', b'Slovenia'), (b'Somalia', b'Somalia'), (b'South Africa', b'South Africa'), (b'South Korea', b'South Korea'), (b'Spain', b'Spain'), (b'Sri Lanka', b'Sri Lanka'), (b'Sudan', b'Sudan'), (b'Suriname', b'Suriname'), (b'Swaziland', b'Swaziland'), (b'Sweden', b'Sweden'), (b'Switzerland', b'Switzerland'), (b'Syria', b'Syria'), (b'Taiwan', b'Taiwan'), (b'Tajikistan', b'Tajikistan'), (b'Tanzania', b'Tanzania'), (b'Thailand', b'Thailand'), (b'The Vatican', b'The Vatican'), (b'Togo', b'Togo'), (b'Trinidad and Tobago', b'Trinidad and Tobago'), (b'Tunisia', b'Tunisia'), (b'Turkey', b'Turkey'), (b'Turkmenistan', b'Turkmenistan'), (b'Turks and Caicos Islands', b'Turks and Caicos Islands'), (b'Tuvalu', b'Tuvalu'), (b'US Minor Outlying Islands', b'US Minor Outlying Islands'), (b'Uganda', b'Uganda'), (b'Ukraine', b'Ukraine'), (b'United Arab Emirates', b'United Arab Emirates'), (b'United Kingdom', b'United Kingdom'), (b'United States', b'United States'), (b'Uruguay', b'Uruguay'), (b'Uzbekistan', b'Uzbekistan'), (b'Venezuela', b'Venezuela'), (b'Vietnam', b'Vietnam'), (b'Virgin Islands (British)', b'Virgin Islands (British)'), (b'Virgin Islands (US)', b'Virgin Islands (US)'), (b'Western Sahara', b'Western Sahara'), (b'Yemen', b'Yemen'), (b'Yugoslavia', b'Yugoslavia'), (b'Zambia', b'Zambia'), (b'Zimbabwe', b'Zimbabwe')])),
                ('zipcode', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InvoiceProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product_name', models.CharField(max_length=255)),
                ('product_expiration_date', models.DateField()),
                ('num_jobs_allowed', models.IntegerField()),
                ('purchase_amount', models.DecimalField(max_digits=20, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'The title of the job as you want it to appear.', max_length=255)),
                ('reqid', models.CharField(help_text=b'The Requisition ID from your system, if any.', max_length=50, verbose_name=b'Requisition ID', blank=True)),
                ('description', models.TextField(help_text=b'The job description.')),
                ('apply_link', models.TextField(help_text=b'The URL of the application form.', verbose_name=b'Apply Link', blank=True)),
                ('apply_info', models.TextField(help_text=b'Describe how candidates should apply for this job.', verbose_name=b'Apply Instructions', blank=True)),
                ('is_syndicated', models.BooleanField(default=False, verbose_name=b'Syndicated')),
                ('date_new', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('date_expired', models.DateField(help_text=b'When the job will be automatically removed from the site.')),
                ('is_expired', models.BooleanField(default=False, help_text=b'Mark this job as expired to remove it from any site(s). This does <b>not</b> delete the job.', verbose_name=b'Expired')),
                ('autorenew', models.BooleanField(default=False, help_text=b'Automatically renew this job for an additional 30 days whenever it expires.', verbose_name=b'Auto-Renew')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guid', models.CharField(default=b'', unique=True, max_length=255, blank=True)),
                ('city', models.CharField(help_text=b'The city where the job is located.', max_length=255)),
                ('state', models.CharField(help_text=b'The state where the job is located.', max_length=200, verbose_name='State/Region')),
                ('state_short', models.CharField(max_length=3, blank=True)),
                ('country', models.CharField(help_text=b'The country where the job is located.', max_length=200, choices=[(b'Afghanistan', b'Afghanistan'), (b'Albania', b'Albania'), (b'Algeria', b'Algeria'), (b'American Samoa', b'American Samoa'), (b'Andorra', b'Andorra'), (b'Angola', b'Angola'), (b'Anguilla', b'Anguilla'), (b'Antartica', b'Antartica'), (b'Antigua and Barbuda', b'Antigua and Barbuda'), (b'Argentina', b'Argentina'), (b'Armenia', b'Armenia'), (b'Aruba', b'Aruba'), (b'Australia', b'Australia'), (b'Austria', b'Austria'), (b'Azerbaijan', b'Azerbaijan'), (b'Bahamas', b'Bahamas'), (b'Bahrain', b'Bahrain'), (b'Bangladesh', b'Bangladesh'), (b'Barbados', b'Barbados'), (b'Belarus', b'Belarus'), (b'Belgium', b'Belgium'), (b'Belize', b'Belize'), (b'Benin', b'Benin'), (b'Bermuda', b'Bermuda'), (b'Bhutan', b'Bhutan'), (b'Bolivia', b'Bolivia'), (b'Bosnia', b'Bosnia'), (b'Botswana', b'Botswana'), (b'Brazil', b'Brazil'), (b'Brunei Darussalam', b'Brunei Darussalam'), (b'Bulgaria', b'Bulgaria'), (b'Burkina Faso', b'Burkina Faso'), (b'Burundi', b'Burundi'), (b'Cambodia', b'Cambodia'), (b'Cameroon', b'Cameroon'), (b'Canada', b'Canada'), (b'Cape Verde', b'Cape Verde'), (b'Cayman Islands', b'Cayman Islands'), (b'Central African Republic', b'Central African Republic'), (b'Chad', b'Chad'), (b'Chile', b'Chile'), (b'China', b'China'), (b'Colombia', b'Colombia'), (b'Comoros', b'Comoros'), (b'Congo', b'Congo'), (b'Cook Islands', b'Cook Islands'), (b'Costa Rica', b'Costa Rica'), (b"Cote D'Ivoire", b"Cote D'Ivoire"), (b'Croatia', b'Croatia'), (b'Cuba', b'Cuba'), (b'Cyprus', b'Cyprus'), (b'Czech Republic', b'Czech Republic'), (b'Denmark', b'Denmark'), (b'Djibouti', b'Djibouti'), (b'Dominica', b'Dominica'), (b'Dominican Republic', b'Dominican Republic'), (b'East Timor', b'East Timor'), (b'Ecuador', b'Ecuador'), (b'Egypt', b'Egypt'), (b'El Salvador', b'El Salvador'), (b'Equatorial Guinea', b'Equatorial Guinea'), (b'Eritrea', b'Eritrea'), (b'Estonia', b'Estonia'), (b'Ethiopia', b'Ethiopia'), (b'Falkland Islands', b'Falkland Islands'), (b'Faroe Islands', b'Faroe Islands'), (b'Fiji', b'Fiji'), (b'Finland', b'Finland'), (b'France', b'France'), (b'French Guiana', b'French Guiana'), (b'French Polynesia', b'French Polynesia'), (b'Gabon', b'Gabon'), (b'Gambia', b'Gambia'), (b'Georgia', b'Georgia'), (b'Germany', b'Germany'), (b'Ghana', b'Ghana'), (b'Gibraltar', b'Gibraltar'), (b'Greece', b'Greece'), (b'Greenland', b'Greenland'), (b'Grenada', b'Grenada'), (b'Guadeloupe', b'Guadeloupe'), (b'Guatemala', b'Guatemala'), (b'Guinea', b'Guinea'), (b'Guinea-bissau', b'Guinea-bissau'), (b'Guyana', b'Guyana'), (b'Haiti', b'Haiti'), (b'Honduras', b'Honduras'), (b'Hong Kong', b'Hong Kong'), (b'Hungary', b'Hungary'), (b'Iceland', b'Iceland'), (b'India', b'India'), (b'Indonesia', b'Indonesia'), (b'Iran', b'Iran'), (b'Iraq', b'Iraq'), (b'Ireland', b'Ireland'), (b'Israel', b'Israel'), (b'Italy', b'Italy'), (b'Jamaica', b'Jamaica'), (b'Japan', b'Japan'), (b'Jordan', b'Jordan'), (b'Kazakhstan', b'Kazakhstan'), (b'Kenya', b'Kenya'), (b'Kuwait', b'Kuwait'), (b'Kyrgyzstan', b'Kyrgyzstan'), (b'Laos', b'Laos'), (b'Latvia', b'Latvia'), (b'Lebanon', b'Lebanon'), (b'Lesotho', b'Lesotho'), (b'Liberia', b'Liberia'), (b'Libyan Arab Jamahiriya', b'Libyan Arab Jamahiriya'), (b'Liechtenstein', b'Liechtenstein'), (b'Lithuania', b'Lithuania'), (b'Luxembourg ', b'Luxembourg '), (b'Macau', b'Macau'), (b'Macedonia', b'Macedonia'), (b'Madagascar', b'Madagascar'), (b'Malawi', b'Malawi'), (b'Malaysia', b'Malaysia'), (b'Maldives', b'Maldives'), (b'Mali', b'Mali'), (b'Malta', b'Malta'), (b'Marshall Islands', b'Marshall Islands'), (b'Martinique', b'Martinique'), (b'Mauritania', b'Mauritania'), (b'Mauritius', b'Mauritius'), (b'Mexico', b'Mexico'), (b'Micronesia', b'Micronesia'), (b'Moldova', b'Moldova'), (b'Monaco', b'Monaco'), (b'Mongolia', b'Mongolia'), (b'Montserrat', b'Montserrat'), (b'Morocco', b'Morocco'), (b'Mozambique', b'Mozambique'), (b'Multiple Asian Countries', b'Multiple Asian Countries'), (b'Multiple European Countries', b'Multiple European Countries'), (b'Myanmar', b'Myanmar'), (b'Namibia', b'Namibia'), (b'Nepal', b'Nepal'), (b'Netherlands', b'Netherlands'), (b'New Zealand', b'New Zealand'), (b'Nicaragua', b'Nicaragua'), (b'Niger', b'Niger'), (b'Nigeria', b'Nigeria'), (b'North Korea', b'North Korea'), (b'Northern Mariana Islands', b'Northern Mariana Islands'), (b'Norway', b'Norway'), (b'Oman', b'Oman'), (b'Pakistan', b'Pakistan'), (b'Palau', b'Palau'), (b'Palestine', b'Palestine'), (b'Panama', b'Panama'), (b'Papua New Guinea', b'Papua New Guinea'), (b'Paraguay', b'Paraguay'), (b'Peru', b'Peru'), (b'Philippines', b'Philippines'), (b'Poland', b'Poland'), (b'Portugal', b'Portugal'), (b'Qatar', b'Qatar'), (b'Reunion Island', b'Reunion Island'), (b'Romania', b'Romania'), (b'Russia', b'Russia'), (b'Rwanda', b'Rwanda'), (b'Saint Kitts and Nevis', b'Saint Kitts and Nevis'), (b'Samoa', b'Samoa'), (b'San Marino', b'San Marino'), (b'Sao Tome and Principe', b'Sao Tome and Principe'), (b'Saudi Arabia', b'Saudi Arabia'), (b'Senegal', b'Senegal'), (b'Serbia and Montenegro', b'Serbia and Montenegro'), (b'Seychelles', b'Seychelles'), (b'Sierra Leone', b'Sierra Leone'), (b'Singapore', b'Singapore'), (b'Slovak Republic', b'Slovak Republic'), (b'Slovenia', b'Slovenia'), (b'Somalia', b'Somalia'), (b'South Africa', b'South Africa'), (b'South Korea', b'South Korea'), (b'Spain', b'Spain'), (b'Sri Lanka', b'Sri Lanka'), (b'Sudan', b'Sudan'), (b'Suriname', b'Suriname'), (b'Swaziland', b'Swaziland'), (b'Sweden', b'Sweden'), (b'Switzerland', b'Switzerland'), (b'Syria', b'Syria'), (b'Taiwan', b'Taiwan'), (b'Tajikistan', b'Tajikistan'), (b'Tanzania', b'Tanzania'), (b'Thailand', b'Thailand'), (b'The Vatican', b'The Vatican'), (b'Togo', b'Togo'), (b'Trinidad and Tobago', b'Trinidad and Tobago'), (b'Tunisia', b'Tunisia'), (b'Turkey', b'Turkey'), (b'Turkmenistan', b'Turkmenistan'), (b'Turks and Caicos Islands', b'Turks and Caicos Islands'), (b'Tuvalu', b'Tuvalu'), (b'US Minor Outlying Islands', b'US Minor Outlying Islands'), (b'Uganda', b'Uganda'), (b'Ukraine', b'Ukraine'), (b'United Arab Emirates', b'United Arab Emirates'), (b'United Kingdom', b'United Kingdom'), (b'United States', b'United States'), (b'Uruguay', b'Uruguay'), (b'Uzbekistan', b'Uzbekistan'), (b'Venezuela', b'Venezuela'), (b'Vietnam', b'Vietnam'), (b'Virgin Islands (British)', b'Virgin Islands (British)'), (b'Virgin Islands (US)', b'Virgin Islands (US)'), (b'Western Sahara', b'Western Sahara'), (b'Yemen', b'Yemen'), (b'Yugoslavia', b'Yugoslavia'), (b'Zambia', b'Zambia'), (b'Zimbabwe', b'Zimbabwe')])),
                ('country_short', models.CharField(help_text=b'The country where the job is located.', max_length=3, blank=True)),
                ('zipcode', models.CharField(help_text=b'The postal code of the job location.', max_length=15, verbose_name='Postal Code', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfflineProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product_quantity', models.PositiveIntegerField(default=1)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfflinePurchase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('redemption_uid', models.CharField(max_length=255)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('redeemed_on', models.DateField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('cost', models.DecimalField(help_text=b'How much this product should cost.', verbose_name=b'Product Price', max_digits=20, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('posting_window_length', models.IntegerField(default=30, help_text=b'The number of days the customer has to post jobs.', verbose_name=b'Posting Window Duration', choices=[(30, b'30 Days'), (60, b'60 Days'), (90, b'90 Days'), (365, b'1 Year')])),
                ('max_job_length', models.PositiveIntegerField(default=30, help_text=b'Number of days each job may appear.', verbose_name=b'Maximum Job Duration', choices=[(15, b'15 Days'), (30, b'30 Days'), (60, b'60 Days'), (90, b'90 Days'), (365, b'1 Year')])),
                ('num_jobs_allowed', models.PositiveIntegerField(default=5, verbose_name=b'Number of Jobs')),
                ('description', models.TextField(verbose_name=b'Product Description')),
                ('featured', models.BooleanField(default=False)),
                ('requires_approval', models.BooleanField(default=True, help_text=b'Jobs posted will require administrator approval.', verbose_name=b'Requires Approval')),
                ('is_archived', models.BooleanField(default=False, help_text=b'', verbose_name=b'Archived')),
                ('is_displayed', models.BooleanField(default=False, help_text=b'Products should show up in the online product lists.', verbose_name=b'Displayed')),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductGrouping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_order', models.IntegerField(default=0, help_text=b'The position in which this group will be displayed to the customer on the product group page.', verbose_name=b'Display Order')),
                ('display_title', models.CharField(help_text=b'The product grouping title as it will be displayed to the user.', max_length=255, verbose_name=b'Display Title')),
                ('explanation', models.TextField(help_text=b'The explanation of the grouping as it will be displayed to the user.')),
                ('name', models.CharField(help_text=b'The "short" name of the product grouping. This is only used in the admin.', max_length=255)),
                ('is_displayed', models.BooleanField(default=True, help_text=b'If "checked" this group will be displayed to the customer on the product group page.', verbose_name=b'Is Displayed')),
            ],
            options={
                'ordering': ['display_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PurchasedJob',
            fields=[
                ('job_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='postajob.Job')),
                ('max_expired_date', models.DateField(editable=False)),
                ('is_approved', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('postajob.job',),
        ),
        migrations.CreateModel(
            name='PurchasedProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('purchase_date', models.DateField(auto_now_add=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('purchase_amount', models.DecimalField(max_digits=20, decimal_places=2)),
                ('expiration_date', models.DateField()),
                ('num_jobs_allowed', models.IntegerField()),
                ('max_job_length', models.IntegerField()),
                ('jobs_remaining', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField()),
                ('action_taken', models.BooleanField(default=False)),
                ('made_on', models.DateField(auto_now_add=True)),
                ('deny_reason', models.TextField(verbose_name='Reason for denying this request', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SitePackage',
            fields=[
                ('package_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='postajob.Package')),
            ],
            options={
            },
            bases=('postajob.package',),
        ),
    ]
