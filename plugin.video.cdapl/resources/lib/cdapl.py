# -*- coding: utf-8 -*-

import sys
from .tools import PY3, U
from collections import namedtuple, OrderedDict
# from multiprocessing.pool import ThreadPool
if PY3:
    from http import cookiejar as cookielib
    from urllib.parse import unquote, urlencode
    from html import entities as htmlentitydefs
    basestring = str
    unicode = str
else:
    import cookielib
    from urllib import unquote, urlencode
    import htmlentitydefs
from .tools import urlparse
import re, os
import json
from . import jsunpack
import xbmcaddon
import xbmcgui
import requests
from .tools import find_re
import xbmc  # log


#: User folder content (sub-folders, items, etc.)
UserFolder = namedtuple('UserFolder', 'folders items pagination tree')

#: Single folder item, "url" is path only
Folder = namedtuple('Folder', 'name id url')

#: Login status info tuple
LoginInfo = namedtuple('LoginInfo', 'logged premium username')

#: Web Request
Request = namedtuple('Request', 'url data headers id')
Request.__new__.__defaults__ = (None, None, None)

#: Web Response
Response = namedtuple('Response', 'content status req')
Response.__new__.__defaults__ = (None, )
Response.url = property(lambda self: self.req.url)


BASEURL='https://www.cda.pl'
TIMEOUT = 10
my_addon        = xbmcaddon.Addon()
kukz =  my_addon.getSetting('loginCookie')
COOKIEFILE = ''
addon_data = None
sess= requests.Session()
sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)
cj=sess.cookies


def getUrl(url, data=None, cookies=None, refer=False, return_response=False):
    if not cookies and kukz:
        cookies = kukz
    elif COOKIEFILE and os.path.exists(COOKIEFILE):
        cj.load(COOKIEFILE)
        cookies = ';'.join('%s=%s' % (c.name, c.value) for c in cj)
    headersok = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'TE': 'Trailers',}
    if refer:
        headersok.update({'Referer': url, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/json'})

    if cookies:
        headersok.update({'Cookie': cookies})

    xbmc.log('CDA: getUrl(url=%r, data=%r)' % (url, data))
    try:
        if data:
            resp = sess.post(url, headers=headersok, data=data)
        else:
            resp = sess.get(url, headers=headersok)
        # content = resp if return_response else resp.content
        content = resp if return_response else resp.text
    except Exception as exc:
        print(exc)
        content = None if return_response else ''
    return content

# def multiGetUrl(urls, cookies=None, refer=False):
#     """Get many URLs from the same host at once. Headers not supportet yet."""
#     def fetch_url(req):
#         if not isinstance(req, Request):
#             req = Request(url)
#         resp = getUrl(req.url, data=req.data, cookies=cookies, refer=refer,
#                       return_response=True)
#         return Response(resp.content, resp.status_code, req)
#
#     return ThreadPool().map(fetch_url, urls)

def CDA_login(USER, PASS, COOKIEFILE):
    my_addon.setSetting('loginCookie', '')
    status = False
    typ = False
    username = USER
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Referer': 'https://www.cda.pl/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
        }

        data = {
            'username': USER,
            'password': PASS,
            'login_submit': ''
        }

        response = sess.post('https://www.cda.pl/login', headers=headers, data=data)
        ab = response.cookies
        ac = sess.cookies
        content = response.text.replace("'", '"')

        rodzaj = re.search('Twoje konto:(.+?)</span>|(Premium aktywne)', content)
        if rodzaj:
            ac.save(COOKIEFILE, ignore_discard=True)
            cookies = ';'.join('%s=%s' % (c.name, c.value) for c in cj)

            if 'darmowe' in rodzaj.group(0):  # whole matched string
                my_addon.setSetting('premka', 'false')
            else:
                my_addon.setSetting('premka', 'true')
                typ=True
            my_addon.setSetting('loginCookie', cookies)
            status=True
            rx = re.search(r'href="(?:https://www.cda.pl)?/([^/"]+)/powiadomienia"', content)
            if rx:
                username = rx.group(1)
        else:
            cj.clear()
            cj.save(COOKIEFILE, ignore_discard=True)
            my_addon.setSetting('loginCookie', '')
    except Exception as exc:
        print('Login failed', exc)
    return LoginInfo(status, typ, username)

def _get_encoded_unpaker(content):
    src =''
    packedMulti = re.compile('eval(.*?)\\{\\}\\)\\)',re.DOTALL).findall(content)
    for packed in packedMulti:
        packed=re.sub('  ',' ',packed)
        packed=re.sub('\n','',packed)
        try:
            unpacked = jsunpack.unpack(packed)
        except:
            unpacked=''
        if unpacked:
            unpacked=re.sub('\\\\','',unpacked)
            src1 = re.compile('[\'"]*file[\'"]*:\\s*[\'"](.+?)[\'"],',  re.DOTALL).search(unpacked)
            src2 = re.compile('[\'"]file[\'"][:\\s]*[\'"](.+?)[\'"]',  re.DOTALL).search(unpacked)
            src3 = re.search('[\'"]file[\'"]:[\'"](.*?\\.mp4)[\'"]',unpacked)
            if src1:
                src = src1.group(1)
            elif src2:
                src = src2.group(1)
            elif src3:
                src = src3.group(1)+'.mp4'
            if src:
                break
    return src

def _get_encoded(content):
    src=''
    idx1 = content.find('|||http')
    if  idx1>0:
        idx2 = content.find('.split', idx1)
        encoded =content[ idx1: idx2]
        if encoded:
            tmp = encoded.split('player')[0]
            tmp=re.sub('[|]+\\w{2,3}[|]+','|',tmp,re.DOTALL)
            tmp=re.sub('[|]+\\w{2,3}[|]+','|',tmp,re.DOTALL)
            remwords=['http','cda','pl','logo','width','height','true','static','st','mp4','false','video','static',
                    'type','swf','player','file','controlbar','ads','czas','position','duration','bottom','userAgent',
                    'match','png','navigator','id', '37', 'regions', '09', 'enabled', 'src', 'media']
            remwords=['http', 'logo', 'width', 'height', 'true', 'static', 'false', 'video', 'player',
                'file', 'type', 'regions', 'none', 'czas', 'enabled', 'duration', 'controlbar', 'match', 'bottom',
                'center', 'position', 'userAgent', 'navigator', 'config', 'html', 'html5', 'provider', 'black',
                'horizontalAlign', 'canFireEventAPICalls', 'useV2APICalls', 'verticalAlign', 'timeslidertooltipplugin',
                'overlays', 'backgroundColor', 'marginbottom', 'plugins', 'link', 'stretching', 'uniform', 'static1',
                'setup', 'jwplayer', 'checkFlash', 'SmartTV', 'v001', 'creme', 'dock', 'autostart', 'idlehide', 'modes',
               'flash', 'over', 'left', 'hide', 'player5', 'image', 'KLIKNIJ', 'companions', 'restore', 'clickSign',
                'schedule', '_countdown_', 'countdown', 'region', 'else', 'controls', 'preload', 'oryginalne', 'style',
                '620px', '387px', 'poster', 'zniknie', 'sekund', 'showAfterSeconds', 'images', 'Reklama', 'skipAd',
                 'levels', 'padding', 'opacity', 'debug', 'video3', 'close', 'smalltext', 'message', 'class', 'align',
                  'notice', 'media']
            for one in remwords:
                tmp=tmp.replace(one,'')
            cleanup=tmp.replace('|',' ').split()
            out={'server': '', 'e': '', 'file': '', 'st': ''}
            if len(cleanup)==4:
                for one in cleanup:
                    if one.isdigit():
                        out['e']=one
                    elif re.match('[a-z]{2,}\\d{3}',one) and len(one)<10:
                        out['server'] = one
                    elif len(one)==22:
                        out['st'] = one
                    else:
                        out['file'] = one
                src='https://%s.cda.pl/%s.mp4?st=%s&e=%s'%(out.get('server'),out.get('file'),out.get('st'),out.get('e'))
    return src

url='https://www.cda.pl/video/14039055a'
url='https://www.cda.pl/video/151660966?wersja=720p'

def scanforVideoLink(content):
    '\n    Scans for video link included encoded one\n    '
    playerdata = re.compile('"video":({.+?})',re.DOTALL).search(content)

    playerdata = playerdata.group(1) if playerdata else ''
    if playerdata:
        out=[]
        pdata = json.loads(playerdata)
        drm_url = pdata['manifest_drm_proxy']
        custom_data = pdata['manifest_drm_pr_header']
        mpd_url = pdata['manifest']
        if mpd_url:
            out.append({'manifest': mpd_url, 'drmheader': custom_data,'drm_url':drm_url})
            return out[0]
    video_link=''
    src1 = re.compile('[\'"]file[\'"][:\\s]*[\'"](.+?)[\'"]',re.DOTALL).search(content)
    player_data = re.findall('player_data="(.*?)"',content,re.DOTALL)
    player_data=player_data[0] if player_data else ''
    unpacked = player_data.replace('&quot;','"')
    file_data = re.compile('[\'"]*file[\'"]*:\\s*[\'"](.+?)[\'"],',  re.DOTALL).search(unpacked)
    if src1:
        video_link = src1.group(1)
    elif file_data:
        video_link = file_data.group(1)
    else:
        video_link = _get_encoded_unpaker(content)
        if not video_link:
            video_link = _get_encoded(content)
    video_link = video_link.replace('\\', '')
    def cdadecode(videofile):
        videofile = cda_replace('1', videofile) ############
        a = videofile
        cc =len(a)
        linkvid=''
        for e in range(cc):
            f = ord(a[e])
            if f >=33 or f <=126:
                b=chr(33 + (f + 14) % 94)
            else:
                b=chr(f)
            linkvid+=b
        if not linkvid.endswith('.mp4'):
            linkvid += '.mp4'
        linkvid = cda_replace('2', linkvid) ############
        if not linkvid.startswith('http'):
            linkvid = 'https://'+linkvid
        return linkvid
    video_link = cdadecode(unquote(video_link))
    if video_link.startswith('uggc'):
        zx = lambda x: 0 if not x.isalpha() else -13 if 'A' <=x.upper()<='M' else 13
        video_link = ''.join([chr((ord(x)-zx(x)) ) for x in video_link])
        video_link=video_link[:-7] + video_link[-4:]
    return video_link
########################################################

def cda_replace(match, link):
    data = getUrl('https://www.cda.pl/js/player.js')
    if match == '1':
        data1 = getDataBeetwenMarkers(data, '11:344', ';return', False)[1]
        dane1 = re.compile('replace\((.+?)\)', re.DOTALL).findall(data1)
        for i in range(len(dane1)):
            rep = dane1[i]
            item = rep.split(',')
            a = item[0].replace('"','')
            b = item[1].replace('"','')
            link = link.replace(a, b)
        return link
    else:
        data2 = getDataBeetwenMarkers(data, 'da=function', '}};', False)[1]
        dane2 = re.compile('replace\((.+?)\)', re.DOTALL).findall(data2)
        for i in range(len(dane2)):
            rep = dane2[i]
            item = rep.split(',')
            a = item[0].replace('"','')
            b = item[1].replace('"','')
            link = link.replace(a, b)
        return link

def getDataBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
    if caseSensitive:
        idx1 = data.find(marker1)
    else:
        idx1 = data.lower().find(marker1.lower())
    if -1 == idx1: return False, ''
    if caseSensitive:
        idx2 = data.find(marker2, idx1 + len(marker1))
    else:
        idx2 = data.lower().find(marker2.lower(), idx1 + len(marker1))
    if -1 == idx2: return False, ''
    if withMarkers:
        idx2 = idx2 + len(marker2)
    else:
        idx1 = idx1 + len(marker1)
    return True, data[idx1:idx2]
#########################################

def getVideoUrls(url, tryIT=4):

    "\n    returns \n        - ulr https://....\n        - or list of [('720p', 'https://www.cda.pl/video/1946991f?wersja=720p'),...]\n         \n    "
    url = url.replace('/vfilm','')
    url = url.replace('?from=catalog','')

    if not 'ebd.cda.pl' in url:
        url='https://ebd.cda.pl/100x100/' + url.split('/')[-1]
    playerSWF = '|Cookie=PHPSESSID=1&Referer=http://static.cda.pl/flowplayer/flash/flowplayer.commercial-3.2.18.swf'
    content = getUrl(url, cookies=kukz)

    src=[]
    if content == '':
        src.append(('Materia\xc5\x82 zosta\xc5\x82 usuni\xc4\x99ty', ''))
    lic1 = content.find('To wideo jest niedost\xc4\x99pne ')

    if lic1 > 0:
        src.append(('To wideo jest niedost\xc4\x99pne w Twoim kraju', ''))
    elif not '?wersja' in url and not 'drmtoday.com' in content:
        quality_options = re.findall('<a data-quality="(.*?)" (?P<H>.*?)>(?P<Q>.*?)</a>', content, re.DOTALL)
        for quality in quality_options:
            link = re.search('href="(.*?)"', quality[1])
            hd = quality[2]
            if link:
                src.insert(0, (hd, link.group(1)))
    if not src:
        src = scanforVideoLink(content)
        if src and not 'drmheader' in str(src):
            src += playerSWF
        if not src:
            for i in range(tryIT):
                content = getUrl(url)
                src = scanforVideoLink(content)
                if src:
                    src += playerSWF
                    break
    if not src:
        if content.find('Ten film jest dost'):
            src=[('Ten film jest dost\xc4\x99pny dla u\xc5\xbcytkownik\xc3\xb3w premium. '
                  'Wtyczka mo\xc5\xbce nie obs\xc5\x82ugiwa\xc4\x87 poprawnie zasob\xc3\xb3w premium','')]
    return src

# def getVideoUrlsQuality(url,quality=0):
#     '\n    returns url to video\n    '
#     src = getVideoUrls(url)
#     if type(src)==list:
#         selected=src[quality]
#         src = getVideoUrls(selected[1])
#     return src

url='https://www.cda.pl/ratownik99/folder-glowny/2'

def _user_folder_content(url, content=None):
    fid = find_re(r'/folder/(\w+)(?:[?].*)?$', url) or 'root'
    if content is None:
        content = getUrl(url)
    if "folderinputPassword" in content:
        passwd = None
        if addon_data:
            passkey = 'folders.folder.%s.pass' % fid
            passwd = addon_data.get(passkey) or addon_data.get('folders.lastpass')
            if passwd:
                # try tu use remembered password
                content = getUrl(url, data={"folderinputPassword" : passwd})
                if not content or 'folderinputPassword' in content:
                    passwd = ''
                    addon_data.remove(passkey)
                elif not addon_data.get(passkey):
                    # save password matching to new folder
                    addon_data.set(passkey, passwd)
        if not passwd:
            passwd = xbmcgui.Dialog().input(u'Hasło do folderu', type=xbmcgui.INPUT_ALPHANUM)
            content = getUrl(url, data={"folderinputPassword" : passwd})
            if passwd:
                if not content or 'folderinputPassword' in content:
                    xbmcgui.Dialog().notification('Złe hasło', 'Hasło do folderu nie jest prawidłowe',
                                                  xbmcgui.NOTIFICATION_ERROR)
                elif addon_data:
                    addon_data.set(passkey, passwd)
                    addon_data.set('folders.lastpass', passwd)
    return content

def _scan_UserFolder(url, recursive=True, items=None, folders=None):
    content = _user_folder_content(url)
    folder_tree = []
    for rx in re.finditer(r'<span class="folder-one-line.*?href="(?P<url>[^"]*?(?P<id>\d*))"[^>]*>(?P<name>[^<]*)<', content):
        data = rx.groupdict()
        data['name'] = PLchar(data['name']).decode('utf8')
        data['url'] = getDobryUrl(data['url'])
        folder_tree.append(Folder(**data))
    if folder_tree and folder_tree[0].name == u'Folder główny':
        userfolder = find_re(r'<a class="[^"]*\blogin-txt\b[^"]*" href="(.*?)"', content)
        if userfolder:
            folder_tree[0] = folder_tree[0]._replace(url='%s/folder-glowny' % getDobryUrl(userfolder))
    if items is None:
        items = []
    if folders is None:
        folders = []
    ids = [(a.start(), a.end()) for a in re.finditer('data-file_id="', content)]
    ids.append( (-1,-1) )
    for i in range(len(ids[:-1])):
        subset  = content[ ids[i][1]:ids[i+1][0] ]
        match   = re.compile('class="link-title-visit" href="(.*?)">(.*?)</a>').findall(subset)
        matchT  = re.compile('class="time-thumb-fold">(.*?)</span>').findall(subset)
        matchHD = re.compile('class="thumbnail-hd-ico">(.*?)</span>').findall(subset)
        matchHD = [a.replace('<span class="hd-ico-elem">','') for a in matchHD]
        matchIM = re.compile('<img[ \t\n]+class="thumb thumb-bg thumb-size"[ \t\n]+alt="(.*?)"[ \t\n]+src="(.*?)">',re.DOTALL).findall(subset)
        if match:
            url = BASEURL+ match[0][0]
            title = PLchar(match[0][1])
            duration =  getDuration(matchT[0]) if matchT else ''
            code = matchHD[0] if matchHD else ''
            plot = PLchar(matchIM[0][0]) if matchIM else ''
            img = getDobryUrlImg(matchIM[0][1]) if matchIM else ''
            items.append({'url':url,'title':unicode(title,'utf-8'),'code':code.encode('utf-8'),'plot':unicode(plot,'utf-8'),'img':img,'duration':duration})

    folders_links = re.compile('class="folder-area">[ \t\n]+<a[ \t\n]+href="(.*?)"',re.DOTALL).findall(content)
    folders_names = re.compile('<span[ \t\n]+class="name-folder">(.*?)</span>',re.DOTALL).findall(content)
    if folders_links:
        if len(folders_names) > len(folders_links): folders_names = folders_names[1:]
        for i in range(len(folders_links)):
            folders.append( {'url':folders_links[i],'title': PLchar(html_entity_decode(folders_names[i])) })
    nextpage = re.compile('<div class="paginationControl">[ \t\n]+<a class="btn btn-primary block" href="(.*?)"',re.DOTALL).findall(content)
    nextpage = nextpage[0] if nextpage else False
    prevpage = re.compile('<a href="(.*?)" class="previous">').findall(content)
    prevpage = prevpage[0] if prevpage else False
    pagination = (prevpage,nextpage)
    if recursive and nextpage:
        _scan_UserFolder(nextpage, recursive, items, folders)
    return items, folders, pagination, folder_tree

# def get_UserFolder_obserwowani(url):
#     content = getUrl(url)
#     items = []
#     folders = []
#     match=re.compile('@u\xc5\xbcytkownicy(.*?)<div class="panel-footer"></div>', re.DOTALL).findall(content)
#     if len(match) > 0:
#         data = re.compile('data-user="(.*?)" href="(.*?)"(.*?)src="(.*?)"', re.DOTALL).findall(match[0])
#         for one in data:
#             folders.append( {'url':one[1]+'/folder-glowny','title': html_entity_decode(one[0]),'img':getDobryUrlImg(one[3]) })
#     return items,folders

def get_UserFolder_content(urlF, recursive=True, filtr_items={}):
    items, folders, pagination, tree = _scan_UserFolder(urlF, recursive)
    if recursive:
        pagination = (False, False)
    _items=[]
    if filtr_items:
        cnt=0
        key = filtr_items.keys()[0]
        value = filtr_items[key].encode('utf-8')
        for item in items:
            if value in item.get(key):
                cnt +=1
                _items.append(item)
        items = _items
        print('Filted %d items by [%s in %s]' % (cnt, value, key))
    return UserFolder(items, folders, pagination, tree)

def get_UserFolder_historia(url, recursive=True):
    """Read history and queue movie list."""
    def convert(item):
        item['url'] = getDobryUrl(item['url'])
        item['img'] = getDobryUrl(item['img'])
        for k in ('title', 'plot'):
            item[k] = PLchar(item[k]).decode('utf-8')
        if item.get('duration'):
            item['duration'] = getDuration(item['duration'])
        return item

    re_media = re.compile(r'<div class="media" id="[^"]+-video-(?P<id>\w+)"'
                          r'.*?<img[^>]+alt="(?P<plot>[^"]*)" src="(?P<img>[^"]*)"'
                          r'.*?<span class="time-thumb-fold"[^>]*>(?P<duration>[^<]*)<'
                          r'.*?<a class="link-title-visit" href="(?P<url>[^"]*)">(?P<title>[^<]+)<',
                          re.DOTALL)
    #read page
    content = getUrl(url)
    # find items
    items = [convert(rx.groupdict()) for rx in re_media.finditer(content)]
    # next and previous pages
    pagination = (False, False)
    pbeg = content.find('paginationControl')
    if pbeg != -1:
        pagcontent = content[pbeg : content.find('</div>', pbeg)]
        pagination = (find_re(r'<a href="([^"]*)" class="previous"', pagcontent, False),
                      find_re(r'<a href="([^"]*)" class="next"', pagcontent, False))
    # returns items and folders
    return items, [], pagination

def l2d(l):
    #'\n    converts list to dictionary for safe data picup\n    '
    return dict(zip(range(len(l)),l))

def replacePLch(itemF):
    list_of_special_chars = [
    ('\xc4\x84', 'a'),('\xc4\x85', 'a'),('\xc4\x98', 'e'),('\xc4\x99', 'e'),('\xc3\x93', 'o'),('\xc3\xb3', 'o'),('\xc4\x86', 'c'),
    ('\xc4\x87', 'c'),('\xc5\x81', 'l'),('\xc5\x82', 'l'),('\xc5\x83', 'n'),('\xc5\x84', 'n'),('\xc5\x9a', 's'),('\xc5\x9b', 's'),
    ('\xc5\xb9', 'z'),('\xc5\xba', 'z'),('\xc5\xbb', 'z'),('\xc5\xbc', 'z'),(' ','_')]
    for a,b in list_of_special_chars:
        itemF = itemF.replace(a,b)
    return itemF

def getDuration(duration):
    return sum([a*b for a,b in zip([1,60,3600], map(int,duration.split(':')[::-1]))])

url='https://www.cda.pl/video/show/naznaczony_2010'
url='https://www.cda.pl/video/show/naznaczony_2010?duration=krotkie&section=&quality=all&section=&s=best&section='
url = 'https://www.cda.pl/info/film_pl_2016'

def searchCDA(url,premka=False,opisuj=1):
    url=replacePLch(url)
    content = getUrl(url)
    labels=re.compile('<label(.*?)</label>', re.DOTALL).findall(content)
    nextpage =re.compile('<a class="sbmBigNext btn-my btn-large fiximg" href="(.*?)"').findall(content)
    items=[]
    for label in labels:
        label = html_entity_decode(label)
        typ_prem=''
        if label.find('premium')>0:
            if premka:
                typ_prem ='[COLOR purple](P)[/COLOR]'
            else: continue
        plot = re.compile('title="(.*)"').findall(label)
        image = re.compile('src="(.*)" ').findall(label)
        hd = re.compile('<span class="hd-ico-elem hd-elem-pos">(.*?)</span>').findall(label)
        duration = re.compile('<span class="timeElem">\\s*(.*?)\\s*</span>').findall(label)
        title=re.compile('<a class=".*?" href="(.*/video/.*?)">(.*?)</a>').findall(label)
        nowosc = 'Nowo\xc5\x9b\xc4\x87' if label.find('Nowo\xc5\x9b\xc4\x87')>0 else ''
        rok = ''
        if title:
            if len(title[0])==2:
                url = BASEURL+ title[0][0] if not title[0][0].startswith('http') else title[0][0]
                title = PLchar(title[0][1].split('<')[0].strip())
                duration = getDuration(duration[0]) if duration else ''
                code = typ_prem
                code += hd[0] if hd else ''
                plot = PLchar(plot[0]) if plot else ''
                img = getDobryUrlImg(image[0]) if image else ''
                if opisuj:
                    plot ='[B]%s[/B]\n%s'%(title,plot)
                    title,rok,l1l1ll11lll11l1l_cda_ = cleanTitle(title)
                items.append({'url':url,'title':unicode(title,'utf-8'),'year':rok,'code':code,'plot':unicode(plot,'utf-8'),'img':img,'duration':duration,'new':nowosc,})
    if items and nextpage:
        nextpage = [p for p in nextpage if '/video' in p]
        nextpage = BASEURL+ nextpage[-1] if nextpage else False
    return items,nextpage

def print_toJson(items):
    for i in items:
        print(i.get('title'))
        print('{"title":"%s","url":"%s","code":"%s"}' % (i.get('title'),i.get('url'),i.get('code')))

def cleanTitle(title):
    pattern = re.compile('[(\\[{;,/,\\\\]')
    year=''
    label=''
    relabel = re.compile('(?:lektor|pl|dubbing|napis[y]*)', flags=re.I | re.X).findall(title.lower())
    if relabel:
        label = ' [COLOR lightgreen] %s [/COLOR]' % ' '.join(relabel)
    rmList=['lektor','dubbing',' pl ','full','hd','\\*','720p','1080p','480p','"']
    for rm in rmList:
        title = re.sub(rm,'',title,flags=re.I | re.X)
    rok = re.findall('\\d{4}',title)
    if rok:
        year = rok[-1]
        title = re.sub(rok[-1],'',title)
    title = pattern.split(title)[0]
    return title.strip(), year, label.strip()

url='https://www.cda.pl/video/8512106'
url='https://www.cda.pl/video/145475730'

def getDobryUrl(link):
    if link.startswith('//'):
        link = 'https:'+link
    elif link.startswith('/'):
        link = 'https://www.cda.pl'+link
    elif not link.startswith('http'):
        link=''
    return link

def getDobryUrlImg(img):  # the same effect as in getDobryUrl()?
    if img.startswith('//'):
        return 'https:'+img
    return img

def grabInforFromLink(url):
    if 'www.cda.pl/video/' in url:
        content = _user_folder_content(url)
        plot=re.compile('<meta property="og:description" content="(.*?)"',re.DOTALL).findall(content)
        title=re.compile('<meta property="og:title" content="(.*?)"').findall(content)
        image=re.compile('<meta property="og:image" content="(.*?)"').findall(content)
        userfolder, username = find_re(r'<a class="link-primary" href="(.*?([^"/]+))"', content)
        quality=re.compile('href=".+?wersja=(.+?)"').findall(content)
        duration = re.compile('<meta itemprop=[\'"]duration[\'"] content=[\'"](.*?)[\'"]').findall(content)
        if title:
            title = PLchar(title[0])
            duration =':'.join(re.compile('(\\d+)').findall(duration[0])) if duration else ''
            duration = getDuration(duration) if duration else ''
            # userfolder = getDobryUrl(userfolder)+'/folder-glowny' if userfolder else ''
            userfolder = getDobryUrl(userfolder)
            code = quality[-1] if quality else ''
            plot = PLchar(plot[0]) if plot else ''
            img = getDobryUrlImg(image[0]) if image else ''
            folders = [Folder(name=u'Folder główny', id=0, url='%s/folder-glowny' % userfolder)]  # root folder
            for rx in re.finditer(r'<span class="tree-folder-ico.*?href="(?P<url>[^"]*?(?P<id>\d*))"[^>]*>(?P<name>[^<]*)<', content):
                data = rx.groupdict()
                data['name'] = PLchar(data['name']).decode('utf8')
                data['url'] = getDobryUrl(data['url'])
                folders.append(Folder(**data))
            return {'url': url,
                    'title': unicode(title, 'utf-8'),
                    'code': code,
                    'plot': unicode(plot, 'utf-8'),
                    'img': img,
                    'duration': duration,
                    'user': userfolder,
                    'folders': folders,
                    'username': username,
                    }
    elif '/folder/' in url:
        content = _user_folder_content(url)
        userfolder, username = find_re(r'<a class="[^"]*\blogin-txt\b[^"]*" href="(.*?([^"/]+))"', content)
        # userfolder = getDobryUrl(userfolder)+'/folder-glowny' if userfolder else ''
        userfolder = getDobryUrl(userfolder)
        folders = [Folder(name=u'Folder główny', id=0, url='%s/folder-glowny' % userfolder)]  # root folder
        for rx in re.finditer(r'<span class="folder-one-line.*?href="(?P<url>[^"]*?(?P<id>\d*))"[^>]*>(?P<name>[^<]*)<', content):
            data = rx.groupdict()
            data['name'] = PLchar(data['name']).decode('utf8')
            data['url'] = getDobryUrl(data['url'])
            folders.append(Folder(**data))
        if len(folders) > 1:  # more then root
            if folders[1].name == u'Folder główny':
                # root foler was in top of folders tree
                folders[1] = folders[1]._replace(url=folders[0].url)
                folders.pop(0)
            return {'url': url,
                    'title': folders[-1].name,
                    'user': userfolder,
                    'folders': folders[:-1],  # without current
                    'username': username,
                    }
    return {}

def html_entity_decode_char(m):
    ent = m.group(1)
    if ent.startswith('x'):
        return unichr(int(ent[1:],16))
    try:
        return unichr(int(ent))
    except Exception as exception:
        if ent in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[ent])
        else:
            return ent

def html_entity_decode(string):
    string = string.decode('UTF-8')
    pattern = 'JiM/KFx3Kz8pOw=='
    s = re.compile(pattern.decode('base64')).sub(html_entity_decode_char, string)
    return s.encode('UTF-8')

def ReadJsonFile(jfilename):
    content = '[]'
    if jfilename.startswith('http'):
        content = getUrl(jfilename)
    elif os.path.exists(jfilename):
        with open(jfilename,'r') as f:
            content = f.read()
            if not content:
                content ='[]'
    data=json.loads(html_entity_decode(content))
    return data

def xpath(mydict, path=''):
    elem = mydict
    if path:
        try:
            for x in path.strip('/').split('/'):
                elem = elem.get(x.decode('utf-8'))
        except:
            pass
    return elem


def jsconWalk(data, path):
    lista_katalogow = []
    lista_pozycji = []

    elems = xpath(data, path)
    if isinstance(elems, dict):
        # created directory
        for e, one in elems.items():
            if isinstance(one, basestring):
                lista_katalogow.append({'img': '', 'title': e, 'url': "", "jsonfile": one})
            elif type(one) is dict and 'jsonfile' in one:  # another json file v2
                one['title'] = e  # dodaj tytul
                one['url'] = ''
                lista_katalogow.append(one)
            else:
                lista_katalogow.append({'img': '', 'title': U(e), 'url': path+'/'+e, 'fanart': ''})
        if lista_katalogow:
            lista_katalogow = sorted(lista_katalogow, key=lambda k: (k.get('idx', ''), k.get('title', '')))
    elif type(elems) is list:
        print('List items')
        for one in elems:
            # check if direct link or User folder:
            if one.has_key('url'):
                if 'folder' in one:
                    # just link to folder, get no content
                    lista_katalogow.append(one)
                else:
                    lista_pozycji.append(one)
            elif one.has_key('folder'):        #This is folder in cda.pl get content:
                filtr_items = one.get('flter_item',{})
                show_subfolders = one.get('subfoders',True)
                show_items = one.get('items',True)
                is_recursive = one.get('recursive',True)

                userfolder = get_UserFolder_content(urlF=one.get('folder',''), recursive=is_recursive,
                                                    filtr_items=filtr_items)
                if show_subfolders:
                    lista_katalogow.extend(userfolder.folders)
                if show_items:
                    lista_pozycji.extend(userfolder.items)

    return (lista_pozycji, lista_katalogow)


def jsconWalk2(data,path):
    lista_katalogow = []
    lista_pozycji=[]
    elems = xpath(data,path)
    if type(elems) is dict:
        for e in elems.keys():
            one=elems.get(e)
            if type(one) is str or type(one) is unicode:
                lista_katalogow.append( {'img':'','title':e,'url':'', 'jsonfile' :one} )
            elif type(one) is dict and one.has_key('jsonfile'):
                one['title']=e
                one['url']=''
                lista_katalogow.append( one )
            else:
                if isinstance(e, unicode):
                    e = e.encode('utf8')
                elif isinstance(e, str):
                    e.decode('utf8')
                lista_katalogow.append( {'img':'','title':e,'url':path+'/'+e,'fanart':''} )
        if lista_katalogow:
             lista_katalogow= sorted(lista_katalogow, key=lambda k: (k.get('idx',''),k.get('title','')))
    if type(elems) is list:
        for one in elems:
            if one.has_key('url'):
                lista_pozycji.append( one )
            elif one.has_key('folder'):
                filtr_items = one.get('flter_item',{})
                show_subfolders = one.get('subfoders',True)
                show_items = one.get('items',True)
                is_recursive = one.get('recursive',True)
                userfolder = get_UserFolder_content(urlF=one.get('folder',''), recursive=is_recursive,
                                                    filtr_items=filtr_items)
                if show_subfolders:
                    lista_katalogow.extend(userfolder.folders)
                if show_items:
                    lista_pozycji.extend(userfolder.items)
    return (lista_pozycji,lista_katalogow)

def PLchar(char):
    if type(char) is not str:
        char=char.encode('utf-8')
    s='JiNcZCs7'
    char = re.sub(s.decode('base64'),'',char)
    char = re.sub('<span style="color:#555">','',char)
    char = re.sub('<br\\s*/>','\n',char)
    char = char.replace('&nbsp;','')
    char = char.replace('&lt;br/&gt;',' ')
    char = char.replace('&ndash;','-')
    char = char.replace('&quot;','"').replace('&amp;quot;','"')
    char = char.replace('&oacute;','\xc3\xb3').replace('&Oacute;','\xc3\x93')
    char = char.replace('&amp;oacute;','\xc3\xb3').replace('&amp;Oacute;','\xc3\x93')
    char = char.replace('&amp;','&')
    char = re.sub('&.+;','',char)
    char = char.replace('\\u0105','\xc4\x85').replace('\\u0104','\xc4\x84')
    char = char.replace('\\u0107','\xc4\x87').replace('\\u0106','\xc4\x86')
    char = char.replace('\\u0119','\xc4\x99').replace('\\u0118','\xc4\x98')
    char = char.replace('\\u0142','\xc5\x82').replace('\\u0141','\xc5\x81')
    char = char.replace('\\u0144','\xc5\x84').replace('\\u0144','\xc5\x83')
    char = char.replace('\\u00f3','\xc3\xb3').replace('\\u00d3','\xc3\x93')
    char = char.replace('\\u015b','\xc5\x9b').replace('\\u015a','\xc5\x9a')
    char = char.replace('\\u017a','\xc5\xba').replace('\\u0179','\xc5\xb9')
    char = char.replace('\\u017c','\xc5\xbc').replace('\\u017b','\xc5\xbb')
    return char

def premium_Katagorie():
    url='https://www.cda.pl/premium'
    content = getUrl(url)
    genre = re.compile('<li><a\\s+href="(https://www.cda.pl/premium/.*?)">(.*?)</a>.*?</li>', re.DOTALL).findall(content)
    out=[]
    for one in genre:
        out.append({'title':PLchar(one[1]),'url':one[0]})
    if out:
        out.insert(0,{'title':'[B]Wszystkie filmy[/B]','url':'https://www.cda.pl/premium'})
    return out

url='https://www.cda.pl/premium/seriale-i-miniserie'

def premium_readContent(content):
    ids = [a.start() for a in re.finditer('<span class="cover-area">', content)]
    ids.append(-1)  # without last character, but never mind
    out = []
    for i in xrange(len(ids) - 1):
        item = content[ids[i]:ids[i+1]]
        href = find_re('<a href="(.*?)"', item)
        title= find_re('class="kino-title">(.*?)<', item)
        img = find_re('src="(.*?)"', item)
        quality = re.findall('"cloud-gray">(.*?p)<', item)
        rate = find_re('<span class="marker">(.*?)<', item)
        plot = find_re('<span class="description-cover-container">(.*?)<[/]*span', item, flags=re.DOTALL)
        if title and href:
            try:
                rating = float(rate) if rate else ''
            except:
                rating = ''
            out.append({
                'title': PLchar(title),
                'url': BASEURL+href if not href.startswith('http') else href,
                'img': getDobryUrlImg(img) if img else '',
                'code': quality[-1] if quality else '',
                'rating': rating,
                'plot': PLchar(plot) if plot else ''
                })
    return out

def premium_Sort():
    return {
        'nowo dodane': 'new',
        'alfabetycznie': 'alpha',
        'najlepiej oceniane na Filmweb': 'best',
        'najcz\xc4\x99\xc5\x9bciej oceniane na Filmweb': 'popular',
        'data premiery kinowej': 'release',
        'popularne w ci\xc4\x85gu ostatnich 60 dni': 'views',
        'popularne w ci\xc4\x85gu ostatnich 30 dni': 'views30',
        'popularne w ci\xc4\x85gu ostatnich 7 dni': 'views7',
        'popularne w ci\xc4\x85gu ostatnich 3 dni': 'views3',
    }

def qual_Sort():
    return {
        'Wszystkie': '1,2,3',
        'Wysoka jako\xc5\x9b\xc4\x87 (720p, 1080p)': '1',
        '\xc5\x9arednia jako\xc5\x9b\xc4\x87 (480p)': '2',
        'Niska jako\xc5\x9b\xc4\x87 (360p)': '3',
    }

def premium_Content(url, params=''):
    """Returns premim content and pagination[prev,next].

    Pagination item is False None) if not pagination
    or something else if exists (empty string is valid pagination!).
    Value have to be set as `params` in next call.
    None value is forbiden.
    """
    if not params:
        content = getUrl(url, cookies=kukz)
        out = premium_readContent(content)
        match = re.search(r'katalogLoadMore\(page,"(.*?)","(.*?)",', content)
        if match:
            next_params = '%d_%s_%s' % (2, match.group(1), match.group(2))
        prev_params = False
    else:
        sp = params.split('_')
        myparams = str([int(sp[0]), sp[1], sp[2], {}])
        payload = '{"jsonrpc":"2.0","method":"katalogLoadMore","params":%s,"id":2}' % myparams
        url = urlparse.urlparse(url or '')
        query = OrderedDict(urlparse.parse_qsl(url.query))
        query.pop('sort', None)
        url = urlparse.urlunparse(url._replace(query=urlencode(query)))
        content = getUrl(url, data=payload.replace("'", '"'), refer=True, cookies=kukz)
        jtmp = json.loads(content).get('result') if content else {}
        if jtmp.get('status') =='continue':
            next_params = '%d_%s_%s' % (int(sp[0])+1, sp[1], sp[2])
        else:
            next_params = False
        if int(sp[0]) <= 2:
            prev_params = ''  # first page, no params, but valid pagination
        else:
            prev_params = '%d_%s_%s' % (int(sp[0])-1, sp[1], sp[2])
        out = premium_readContent(jtmp.get('html',''))
    return out, [prev_params, next_params]
