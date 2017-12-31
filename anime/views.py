from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404, Http404
from anime.models import *
import urllib.parse
import re
import requests
from xml.etree import ElementTree
import json

USE_LOCAL_CONFIG = True  # Enable this to use local configuration files (for episodes only)


# Create your views here.
def index(request):
    sources = Series.objects.values_list('source', flat=True).distinct().order_by()
    return render(request, 'anime/index.html', context={
        'souces': sources,
        'series': Series.objects.all(),
    })


def crunchyroll(request):
    page_url = urllib.parse.unquote(request.GET.get('url', '') + '?skip_wall=1')
    offset = request.GET.get('offset', '0')
    page_content = requests.get(page_url).content.decode('utf-8')
    config_url = urllib.parse.unquote(re.search('config_url":"(.*?)auto_play', page_content).group(1))
    config_content = requests.post(config_url, data=dict(current_page=page_url), allow_redirects=True).content
    tree = ElementTree.fromstring(config_content)
    video_480p_url = tree.find('.//{default}preload/stream_info/file').text
    video_480p_filename = re.search('_(.*?).mp4', video_480p_url).group(1)
    video_1080p_filename = str(int(video_480p_filename) + int(offset))
    video_1080p_url = re.sub('%s.mp4' % video_480p_filename, '%s.mp4' % video_1080p_filename, video_480p_url)
    return redirect(video_1080p_url)


def append_playlist_crunchyroll(
        playlist, series, subtitles, episode_number, episode_url, episode_offset,
        episode_poster, episode_thumbnail, episode_name, episode_description):
    sources = []
    source = {
        'src': '/anime/crunchyroll/?url=%s&offset=%s' % (urllib.parse.quote(episode_url), episode_offset),
        'type': 'application/x-mpegURL',
    }
    sources.append(source)
    text_tracks = []
    first_subtitle = True
    for s in subtitles:
        subtitle = {
            'src': '/static/anime/series/%s/%s.%s.vtt' % (series.id, episode_number, s.id),
            'kind': 'captions',
            'srclang': s.srclang,
            'label': s.label,
        }
        if first_subtitle:
            first_subtitle = False
            subtitle['default'] = 1
        text_tracks.append(subtitle)

    playlist.append({
        'sources': sources,
        'textTracks': text_tracks,
        'name': 'Episode %s - %s' % (episode_number, episode_name),
        'poster': episode_poster,
        'thumbnail': episode_thumbnail,
        'description': episode_description,
        'series_title': series.title_en,
    })


def watch_crunchyroll(request, series_id):
    series = get_object_or_404(Series, id=series_id.strip().lower())
    # Render available subtitles
    subtitles = series.subtitles.all()
    subtitles_text = []
    for s in subtitles:
        subtitles_text.append(s.label)
    # Generate playlist
    playlist = []

    if USE_LOCAL_CONFIG:
        with open('anime/static/anime/series/%s/crunchyroll.json' % series_id, 'r') as f:
            episodes = json.load(f)
            for e in episodes:
                episode_number = e['number']
                episode_url = 'http://www.crunchyroll.com/' + series.original_id + '/' + e['page']
                episode_offset = e['offset']
                episode_poster = e['poster']
                episode_thumbnail = re.sub('_full', '_wide', episode_poster)
                episode_name = e['name']
                episode_description = e['description']
                append_playlist_crunchyroll(
                    playlist, series, subtitles, episode_number, episode_url, episode_offset,
                    episode_poster, episode_thumbnail, episode_name, episode_description
                )

    else:
        episodes = get_list_or_404(EpisodeCrunchyroll, series=series)
        for e in episodes:
            episode_number = e.number
            episode_url = 'http://www.crunchyroll.com/' + series.original_id + '/' + e.page
            episode_offset = e.offset
            episode_poster = e.poster
            episode_thumbnail = re.sub('_full', '_wide', episode_poster)
            episode_name = e.name
            episode_description = e.description
            append_playlist_crunchyroll(
                playlist, series, subtitles, episode_number, episode_url, episode_offset,
                episode_poster, episode_thumbnail, episode_name, episode_description
            )

    return render(request, 'anime/watch.html', context={
        'series_title': series.title_en,
        'subtitles': subtitles_text,
        'series_remark': series.remark,
        'playlist': playlist,
    })


def watch(request, series_id):
    site = request.GET.get('site', 'crunchyroll')
    if site == 'crunchyroll':
        return watch_crunchyroll(request, series_id)
    else:
        raise Http404()
