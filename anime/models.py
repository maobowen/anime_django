from django.db import models


# Create your models here.
class Subtitle(models.Model):
    id = models.CharField('Language ID', max_length=8, primary_key=True)  # enUS
    srclang = models.CharField('Language Code', max_length=8)  # en
    label = models.CharField('Language Label', max_length=100)  # English

    def __str__(self):
        return self.id

    class Meta:
        ordering = ['id']


class Series(models.Model):
    id = models.CharField('Series ID', max_length=100, primary_key=True)
    original_id = models.CharField('Series Original ID', max_length=100)
    title_en = models.CharField('Series Title (English)', max_length=100)
    title_zh = models.CharField('Series Title (Chinese)', max_length=100)
    source = models.CharField('Source', max_length=20, default='crunchyroll')
    poster = models.URLField('Series Poster')
    date = models.DateField('Date')
    subtitles = models.ManyToManyField(Subtitle)
    remark = models.TextField('Remarks')
    available = models.BooleanField('Available', default=False)

    def __str__(self):
        return self.id

    class Meta:
        ordering = ['-date', 'title_en']


class EpisodeCrunchyroll(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, verbose_name='Series')
    number = models.SmallIntegerField('Episode Number')
    id = models.CharField('ID', max_length=100, primary_key=True)
    page = models.CharField('Webpage', max_length=200)
    name = models.CharField('Episode Title', max_length=100)
    poster = models.URLField('Episode Poster')
    description = models.TextField('Description')
    duration = models.DurationField('Duration', null=True)
    offset = models.SmallIntegerField('Offset', default=0)

    def __str__(self):
        return self.id

    class Meta:
        unique_together = (("series", "id"),)
        ordering = ['series', 'id']
