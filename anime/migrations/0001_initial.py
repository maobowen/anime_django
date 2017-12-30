# Generated by Django 2.0 on 2017-12-30 22:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EpisodeCrunchyroll',
            fields=[
                ('number', models.CharField(max_length=5, verbose_name='Episode Number')),
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False, verbose_name='ID')),
                ('page', models.CharField(max_length=200, verbose_name='Webpage')),
                ('name', models.CharField(max_length=100, verbose_name='Episode Title')),
                ('poster', models.URLField(verbose_name='Episode Poster')),
                ('description', models.TextField(verbose_name='Description')),
                ('duration', models.DurationField(null=True, verbose_name='Duration')),
                ('offset', models.SmallIntegerField(default=0, verbose_name='Offset')),
            ],
            options={
                'ordering': ['series', 'number'],
            },
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False, verbose_name='Series ID')),
                ('original_id', models.CharField(max_length=100, verbose_name='Series Original ID')),
                ('title_en', models.CharField(max_length=100, verbose_name='Series Title (English)')),
                ('title_zh', models.CharField(max_length=100, verbose_name='Series Title (Chinese)')),
                ('source', models.CharField(default='crunchyroll', max_length=20, verbose_name='Source')),
                ('poster', models.URLField(verbose_name='Series Poster')),
                ('date', models.DateField(verbose_name='Date')),
                ('remark', models.TextField(verbose_name='Remarks')),
                ('available', models.BooleanField(default=False, verbose_name='Available')),
            ],
            options={
                'ordering': ['-date', 'title_en'],
            },
        ),
        migrations.CreateModel(
            name='Subtitle',
            fields=[
                ('id', models.CharField(max_length=8, primary_key=True, serialize=False, verbose_name='Language ID')),
                ('srclang', models.CharField(max_length=8, verbose_name='Language Code')),
                ('label', models.CharField(max_length=100, verbose_name='Language Label')),
                ('priority', models.PositiveSmallIntegerField(default=0, verbose_name='Priority')),
            ],
            options={
                'ordering': ['-priority', 'id'],
            },
        ),
        migrations.AddField(
            model_name='series',
            name='subtitles',
            field=models.ManyToManyField(to='anime.Subtitle'),
        ),
        migrations.AddField(
            model_name='episodecrunchyroll',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anime.Series', verbose_name='Series'),
        ),
        migrations.AlterUniqueTogether(
            name='episodecrunchyroll',
            unique_together={('series', 'number')},
        ),
    ]
