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
        parser.add_argument('--username', dest='username', action='store', help='username (optional)')
        parser.add_argument('--password', dest='password', action='store', help='password (optional)')

    @staticmethod
    def unidecode(string):
        string = re.sub(u'[\u201c\u201d]', '"', string)  # Convert double quotation marks
        string = re.sub(u'[\u2018\u2019]', "'", string)  # Convert single quotation marks
        string = re.sub(u'\u2026', '...', string)  # Convert horizontal ellipsis
        string = re.sub('[\r\n]', '', string)  # Remove newlines
        string = re.sub(u'\u00a0', '', string)  # Remove no-breaking space
        string = re.sub(' +', ' ', string)  # Remove extra spaces
        return string

    @staticmethod
    def get_duration_crunchyroll(page_url):
        page_url = urllib.parse.unquote(page_url + '?skip_wall=1')
        page_content = requests.get(page_url).content.decode('utf-8')
        config_url = urllib.parse.unquote(re.search('config_url":"(.*?)auto_play', page_content).group(1))
        config_content = requests.post(config_url, data=dict(current_page=page_url), allow_redirects=True).content
        tree = ElementTree.fromstring(config_content)
        duration = tree.find('.//{default}preload/stream_info/metadata/duration').text
        return duration

    def get_offset_crunchyroll(self, page_url, username, password, video_1080p_url):
        if username is None or password is None:  # Not premium account
            offset = 2
        else:
            page_url = urllib.parse.unquote(page_url + '?skip_wall=1')
            ydl_opts = {
                'forceurl': True,
                'simulate': True,
                'ignoreerrors': True,
            }
            ydl_opts_premium = {
                'forceurl': True,
                'simulate': True,
                'ignoreerrors': True,
                'username': username,
                'password': password,
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                with youtube_dl.YoutubeDL(ydl_opts_premium) as ydl_premium:
                    video_480p_info = ydl.extract_info(page_url, download=False)
                    video_480p_url = video_480p_info.get('url', None)
                    video_480p_filename = re.search('_(.*?).mp4', video_480p_url).group(1)
                    video_1080p_filename = re.search('_(.*?).mp4', video_1080p_url).group(1)
                    offset = int(video_1080p_filename) - int(video_480p_filename)
                    if offset == 0:
                        offset = 2

        self.stdout.write('Crunchyroll offset: %d' % offset)
        return offset

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
            'ignoreerrors': True,
        }
        if options['username'] is not None and options['password'] is not None:
            ydl_opts['username'] = options['username']
            ydl_opts['password'] = options['password']

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(series_url, download=False)
            all_episodes = list()
            for e in info['entries']:
                if e is not None and not re.search('\(Dub\)', e['title']):
                    season = e['season_number']
                    match = re.search('_S(\d+)$', series_id)
                    if match and season is not None and season != int(match.group(1)):  # Season not match
                        pass
                    else:
                        number = str(e['episode_number'])
                        self.stdout.write('Processing episode %s' % number)
                        page = e['webpage_url_basename']
                        name = Command.unidecode(e['episode'])
                        poster = e['thumbnail']
                        description = Command.unidecode(e['description'])
                        offset = 0
                        if source == 'crunchyroll':
                            offset = self.get_offset_crunchyroll(
                                e['webpage_url'], options['username'], options['password'], e.get('url', None))
                        duration = None
                        if source == 'crunchyroll':
                            duration = Command.get_duration_crunchyroll(e['webpage_url'])
                        parameters = {
                            'number': number,
                            'page': page,
                            'offset': offset,
                            'name': name,
                            'poster': poster,
                            'description': description,
                            'duration': duration,
                        }

                        if options['local']:
                            all_episodes.append(parameters)
                        else:
                            parameters['series'] = series_id
                            all_episodes.append({
                                'model': 'anime.episode%s' % source,
                                'pk': "%s_%s" % (series_id, number),
                                'fields': parameters,
                            })

            json_str = json.dumps(all_episodes, indent=4)
            filename = '%s.json' % source if options['local'] else '%s_fixture.json' % source
            directory = 'anime/static/anime/series/%s/' % series_id
            self.stdout.write('Dumping data to %s' % os.path.join(directory, filename))
            if not os.path.exists(directory):
                os.makedirs(directory)
            with codecs.open(os.path.join(directory, filename), 'w', 'utf-8') as f:
                f.write(json_str)
