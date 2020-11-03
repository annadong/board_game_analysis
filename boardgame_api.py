import urllib.request, urllib.error, urllib.parse
from urllib.error import  URLError
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError as ETParseError
from time import sleep

import logging
import re
from Boardgame import Boardgame

log = logging.getLogger(__name__)


class BGGAPIException(Exception):
    pass


class BGGAPI(object):
    '''
    BGGAPI is a class that knows how to contact BGG for information, parse out relevant details,
    the create a Python BGG object for general use.

    Example:
        api = BGGAPI()

        bg = api.fetch_boardgame('yinsh')
        print 'Yinsh was created in %s by %s' % (bg.year, ', '.join(bg.designers))
    '''
    def __init__(self):
        self.root_url = 'http://www.boardgamegeek.com/xmlapi2/'

    def _fetch_tree(self, url):
        try:
            tree = ET.parse(urllib.request.urlopen(url))
        except URLError as e:
            log.warn('error getting URL: %s' % url)
            if hasattr(e, 'reason'):
                log.warn('We failed to reach a server. Reason: %s' % e.reason)
            elif hasattr(e, 'code'):
                log.warn('The server couldn\'t fulfill the request. Error code: %d', e.code)
            # raise BGGAPIException(e)
            return None
        except ETParseError as e:
            log.critical('unable to parse BGG response to %s' % url)
            # raise BGGAPIException(e)
            return None

        return tree

    def fetch_boardgame(self, name, bgid=None, forcefetch=False):
        '''Fetch information about a bardgame from BGG by name. If bgid is given,
        it will be used instead. bgid is the ID of the game at BGG. bgid should be type str.

        BGGAPI always caches the first fetch of a game if given a cachedir. If forcefetch == True, 
        fetch_boardgame will fetch or re-fetch from BGG.'''
        if bgid is None:
            # ideally we'd search the cache by name, but that would be
            # difficult. So we just fetch it via BGG.
            log.debug('fetching boardgame by name "%s"' % name)
            url = '%ssearch?query=%s&exact=1' % (self.root_url,
                                                 urllib.parse.quote(name))
            tree = self._fetch_tree(url)
            game = tree.find("./*[@type='boardgame']")
            if game is None:
                log.warn('game not found: %s' % name)
                return None

            bgid = game.attrib['id'] if 'id' in game.attrib else None
            if not bgid:
                log.warning('BGGAPI gave us a game without an id: %s' % name)
                return None

        log.debug('fetching boardgame by BGG ID "%s"' % bgid)
        url = '%sthing?id=%s&comments=1' % (self.root_url, bgid)
        tree = self._fetch_tree(url)

        if tree is None:
            return None

        root = tree.getroot()

        kwargs = dict()
        kwargs['bgid'] = bgid
        # entries that use attrib['value'].
        value_map = {
            './/yearpublished': 'year',
            './/minplayers': 'minplayers',
            './/maxplayers': 'maxplayers',
            './/playingtime': 'playingtime',
            './/name': 'names',
            './/comment': 'comments',
            ".//link[@type='boardgamefamily']": 'families',
            ".//link[@type='boardgamecategory']": 'categories',
            ".//link[@type='boardgamemechanic']": 'mechanics',
            ".//link[@type='boardgamedesigner']": 'designers',
            ".//link[@type='boardgameartist']": 'artists',
            ".//link[@type='boardgamepublisher']": 'publishers',
        }
        normal_comments, good_comments, okay_comments, bad_comments = [], [], [], []
        for xpath, bg_arg in value_map.items():
            els = root.findall(xpath)
            for el in els:
                if bg_arg == 'comments':
                    if el.attrib['rating'] == 'N/A':
                        normal_comments.append(el.attrib['value'])
                    elif float(el.attrib['rating']) > 6.5:
                        good_comments.append(el.attrib['value'])
                    elif float(el.attrib['rating']) < 3.5:
                        bad_comments.append(el.attrib['value'])
                    else:
                        okay_comments.append(el.attrib['value'])
                else:
                    if 'value' in el.attrib:
                        if bg_arg in kwargs:
                            # multiple entries, make this arg a list.
                            if type(kwargs[bg_arg]) != list:
                                kwargs[bg_arg] = [kwargs[bg_arg]]
                            kwargs[bg_arg].append(el.attrib['value'])
                        else:
                            kwargs[bg_arg] = el.attrib['value']
                    else:
                        log.warn('no "value" found in %s for game %s' % (xpath, name))
        kwargs['normal_comments'] = normal_comments
        kwargs['good_comments'] = good_comments
        kwargs['bad_comments'] = bad_comments
        kwargs['okay_comments'] = okay_comments

        # entries that use text instead of attrib['value']
        value_map = {
            './thumbnail': 'thumbnail',
            './image': 'image',
            './description': 'description'
        }
        for xpath, bg_arg in value_map.items():
            els = root.findall(xpath)
            if els:
                if len(els) > 0:
                    log.warn('Found multiple entries for %s, ignoring all but first' % xpath)
                kwargs[bg_arg] = els[0].text

        log.debug('creating boardgame with kwargs: %s' % kwargs)
        return Boardgame(**kwargs)
    
    def fetch_reviews(self, boardgame_id, review_size=10):
        # get the id for the reviews for the boardgame requested
        url='{}forumlist?id={}&type=thing'.format(self.root_url, boardgame_id)
        tree = self._fetch_tree(url)
        root = tree.getroot()
        els = root.find(".//forum[@title='Reviews']")
        forum_id = els.attrib['id']

        # get the review thread ids
        url_forum = '{}forum?id={}'.format(self.root_url, forum_id)
        tree_forum = self._fetch_tree(url_forum)
        root_forum = tree_forum.getroot()
        els_forum = root_forum.findall('.//thread')
        thread_ids = [els_forum[i].attrib['id'] for i in range(min(review_size, len(els_forum)))]

        reviews = []
        for thread_id in thread_ids:
            url_threads = '{}threads?id={}'.format(self.root_url, thread_id)
            tree_thread = self._fetch_tree(url_threads)
            root_thread = tree_thread.getroot()
            review = root_thread.find('.//article').find('./body').text
            review_rep = re.sub(r'<.*>', '', review)
            reviews.append(review_rep.replace('\n', ''))
        
        return reviews