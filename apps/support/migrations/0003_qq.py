# Generated by Django 2.0.8 on 2019-04-15 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_banners_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='QQ',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('qq', models.IntegerField()),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
    ]
