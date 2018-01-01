from django.core.management.base import BaseCommand, CommandError
import youtube_dl
import urllib.parse
import re
import requests
from xml.etree import ElementTree
import json
import os
import codecs


class Command(BaseCommand):
    help = 'Generate the configuration file for a series.'

    def add_arguments(self, parser):
        parser.add_argument('series_id', type=str, help='unique id of the series')
        parser.add_argument('series_original_id', type=str, help='original basename of the series')
        parser.add_argument('--source',
                            default='crunchyroll',
                            const='crunchyroll',
                            nargs='?',
                            choices=['crunchyroll', 'funimation', 'hidive'],
                            help='source of the series (default: %(default)s)')
        parser.add_argument('--use-db', dest='local', action='store_false', help='if set, a fixture will be generated')
        parser.set_defaults(local=True)

    @staticmethod
    def get_duration_crunchyroll(page_url):
        page_url = urllib.parse.unquote(page_url + '?skip_wall=1')
        page_content = requests.get(page_url).content.decode('utf-8')
        config_url = urllib.parse.unquote(re.search('config_url":"(.*?)auto_play', page_content).group(1))
        config_content = requests.post(config_url, data=dict(current_page=page_url), allow_redirects=True).content
        tree = ElementTree.fromstring(config_content)
        duration = tree.find('.//{default}preload/stream_info/metadata/duration').text
        return duration

    def handle(self, *args, **options):
        series_id = options['series_id']
        series_original_id = options['series_original_id']
        source = options['source']
        series_url = ''
        if source == 'crunchyroll':
            series_url = 'http://www.crunchyroll.com/%s?skip_wall=1' % series_original_id

        ydl_opts = {
            'forcejson': True,
            'simulate': True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(series_url, download=False)
            all_episodes = list()
            for e in info['entries']:
                self.stdout.write('Processing episode %s' % str(e['episode_number']))
                if not re.search('\(Dub\)', e['title']):
                    number = str(e['episode_number'])
                    page = e['webpage_url_basename']
                    name = e['episode']
                    poster = e['thumbnail']
                    description = e['description']
                    duration = None
                    if source == 'crunchyroll':
                        duration = Command.get_duration_crunchyroll(e['webpage_url'])

                    if options['local']:
                        all_episodes.append({
                            'number': number,
                            'page': page,
                            'offset': 2,
                            'name': name,
                            'poster': poster,
                            'description': description,
                            'duration': duration,
                        })
                    else:
                        all_episodes.append({
                            'model': 'anime.episode%s' % source,
                            'pk': "%s_%s" % (series_id, number),
                            'fields': {
                                'series': series_id,
                                'number': number,
                                'page': page,
                                'offset': 2,
                                'name': name,
                                'poster': poster,
                                'description': description,
                                'duration': duration,
                            },
                        })

            json_str = json.dumps(all_episodes, indent=4)
            filename = '%s.json' % source if options['local'] else '%s_fixture.json' % source
            directory = 'anime/static/anime/series/%s/' % series_id
            self.stdout.write('Dumping data to %s' % os.path.join(directory, filename))
            if not os.path.exists(directory):
                os.makedirs(directory)
            with codecs.open(os.path.join(directory, filename), 'w', 'utf-8') as f:
                f.write(json_str)
