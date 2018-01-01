from django.core.management.base import BaseCommand, CommandError
import youtube_dl
import os
import glob
import re
import subprocess


class Command(BaseCommand):
    help = 'Generate subtitles for a series.'

    def add_arguments(self, parser):
        parser.add_argument('series_id', type=str, help='unique id of the series')
        parser.add_argument('series_original_id', type=str, help='original basename of the series')
        parser.add_argument('--source',
                            default='crunchyroll',
                            const='crunchyroll',
                            nargs='?',
                            choices=['crunchyroll', 'funimation', 'hidive'],
                            help='source of the series (default: %(default)s)')
        parser.add_argument('--username', dest='username', action='store', help='username (optional)')
        parser.add_argument('--password', dest='password', action='store', help='password (optional)')

    def exec(self, arg):
        p = subprocess.Popen(arg, stdout=subprocess.PIPE)
        while p.poll() is None:
            line = p.stdout.readline()
            self.stdout.write(line.decode('utf-8').rstrip())
        self.stdout.write(p.stdout.read().decode('utf-8').rstrip())

    def handle(self, *args, **options):
        series_id = options['series_id']
        series_original_id = options['series_original_id']
        source = options['source']

        directory = 'anime/static/anime/series/%s/' % series_id
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.chdir(directory)
        self.stdout.write('Downloading subtitles to %s' % directory)

        series_url = ''
        if source == 'crunchyroll':
            series_url = 'http://www.crunchyroll.com/%s?skip_wall=1' % series_original_id

        ydl_opts = {
            'writesubtitles': True,
            'allsubtitles': True,
            'skip_download': True,
            'ignoreerrors': True,
            'outtmpl': 'S%(season_number)s_%(title)s-%(id)s.%(ext)s',
        }
        if options['username'] is not None and options['password'] is not None:
            ydl_opts['username'] = options['username']
            ydl_opts['password'] = options['password']

        print(series_url)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([series_url])

            for ass_file in glob.glob('*.ass'):
                sp1 = ass_file.rsplit('.', 2)
                if not re.search('\(Dub\)', sp1[0]):
                    match1 = re.search('_S(\d+)$', series_id)
                    match2 = re.search('^S(\d+)_', sp1[0])
                    if match1 and match2 and int(match1.group(1)) != int(match2.group(1)):  # Season not match
                        pass
                    else:
                        match = re.search(u'Episode\s(.*?)\s[\u2013\u2014]', sp1[0])
                        episode_id = match.group(1) if match else 0
                        vtt_file = '%s.%s.vtt' % (episode_id, sp1[-2])
                        self.exec(['ffmpeg', '-i', ass_file, vtt_file])
                os.remove(ass_file)
