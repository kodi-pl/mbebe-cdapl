# -*- coding: utf-8 -*-

import sys
import cookielib
import urllib2,urllib
import re,os
import json as json
import jsunpack as jsunpack #jsunpack
import xbmcaddon
from urllib import unquote
import requests

BASEURL='https://www.cda.pl'
TIMEOUT = 10
my_addon        = xbmcaddon.Addon()
kukz =  my_addon.getSetting('loginCookie')
COOKIEFILE = ''
sess= requests.Session()
sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)
cj=sess.cookies
def getUrl(url,data=None,cookies=None,Refer=False):
	if COOKIEFILE and os.path.exists(COOKIEFILE):
		cj.load(COOKIEFILE)
		cookies = ';'.join(['%s=%s'%(c.name,c.value) for c in cj])
	headersok = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1',
		'TE': 'Trailers',}	
	if Refer:
		headersok.update({'Referer': url,'X-Requested-With': 'XMLHttpRequest','Content-Type':'application/json'})

	if cookies:
		headersok.update({'Cookie': cookies})

	if data:
		link = sess.post(url,headers=headersok,data=data).content
	else:
		try:
			link = sess.get(url,headers=headersok).content
		except:
			link=''
	return link
def CDA_login(USER,PASS,COOKIEFILE):
	my_addon.setSetting('loginCookie','')
	status=False
	typ=False
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
		ab=response.cookies
		ac=sess.cookies
		contents = (response.content).replace("\'",'"')

		rodzaj = re.findall('Twoje konto:(.+?)</span>',contents)#[0]
		if rodzaj:
			ac.save(COOKIEFILE, ignore_discard = True)
			cookies = ';'.join(['%s=%s'%(c.name,c.value) for c in cj])

			if 'darmowe' in rodzaj[0]:
				
				my_addon.setSetting('premka','false')
			else:
				my_addon.setSetting('premka','true')	
				typ=True
			my_addon.setSetting('loginCookie',cookies)	
			status=True
		else:
			cj.clear()
			cj.save(COOKIEFILE, ignore_discard = True)
			my_addon.setSetting('loginCookie','')
	except:
		pass
	return status,typ
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
		linkvid = linkvid.replace("0)sss.mp4", ".mp4")  
		linkvid = linkvid.replace(".cda.mp4", "").replace(".cda.mp4", "").replace(".2cda.pl", ".cda.pl").replace(".3cda.pl", ".cda.pl");
    	
    	if not linkvid.startswith('http'):
    		linkvid = 'https://'+linkvid
    	return linkvid
    video_link = cdadecode(unquote(video_link))
    if video_link.startswith('uggc'):
        zx = lambda x: 0 if not x.isalpha() else -13 if 'A' <=x.upper()<='M' else 13
        video_link = ''.join([chr((ord(x)-zx(x)) ) for x in video_link])
        video_link=video_link[:-7] + video_link[-4:]
    return video_link
def getVideoUrls(url,tryIT=4):
	
	"\n    returns \n        - ulr https://....\n        - or list of [('720p', 'https://www.cda.pl/video/1946991f?wersja=720p'),...]\n         \n    "
	url = url.replace('/vfilm','')
	url = url.replace('?from=catalog','')
	
	

	if not 'ebd.cda.pl' in url:
		url='https://ebd.cda.pl/100x100/'+url.split('/')[-1]
	playerSWF='|Cookie=PHPSESSID=1&Referer=http://static.cda.pl/flowplayer/flash/flowplayer.commercial-3.2.18.swf'
	content = getUrl(url,cookies=kukz)
	
	src=[]
	if content=='':
		src.append(('Materia\xc5\x82 zosta\xc5\x82 usuni\xc4\x99ty',''))
	lic1 = content.find('To wideo jest niedost\xc4\x99pne ')
	
	if lic1>0:
		src.append(('To wideo jest niedost\xc4\x99pne w Twoim kraju',''))
	elif not '?wersja' in url and not 'drmtoday.com' in content:
		quality_options = re.compile('<a data-quality="(.*?)" (?P<H>.*?)>(?P<Q>.*?)</a>', re.DOTALL).findall(content)
		for quality in quality_options:
			link = re.search('href="(.*?)"',quality[1])
			hd = quality[2]
			if link:
				src.insert(0,(hd,link.group(1)))
	if not src:
		src = scanforVideoLink(content)
		if src and not 'drmheader' in str(src):
			src+=playerSWF
		if not src:
			for i in range(tryIT):
				content = getUrl(url)
				src = scanforVideoLink(content)
				if src:
					src+=playerSWF
					break
	if not src:
		if content.find('Ten film jest dost'):
			src=[('Ten film jest dost\xc4\x99pny dla u\xc5\xbcytkownik\xc3\xb3w premium. Wtyczka mo\xc5\xbce nie obs\xc5\x82ugiwa\xc4\x87 poprawnie zasob\xc3\xb3w premium','')]
	return src
def getVideoUrlsQuality(url,quality=0):
    '\n    returns url to video\n    '
    src = getVideoUrls(url)
    if type(src)==list:
        selected=src[quality]
        src = getVideoUrls(selected[1])
    return src
def getDobryUrlImg(img):
    if img.startswith('//'):
        return 'https:'+img
    else:
        return img
url='https://www.cda.pl/ratownik99/folder-glowny/2'
def _scan_UserFolder(url,recursive=True,items=[],folders=[]):
	content = getUrl(url)
	items = items
	folders = folders
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
		_scan_UserFolder(nextpage,recursive,items,folders)
	return items,folders,pagination
def get_UserFolder_obserwowani(url):
    content = getUrl(url)
    items = []
    folders = []
    match=re.compile('@u\xc5\xbcytkownicy(.*?)<div class="panel-footer"></div>', re.DOTALL).findall(content)
    if len(match) > 0:
        data = re.compile('data-user="(.*?)" href="(.*?)"(.*?)src="(.*?)"', re.DOTALL).findall(match[0])
        for one in data:
            folders.append( {'url':one[1]+'/folder-glowny','title': html_entity_decode(one[0]),'img':getDobryUrlImg(one[3]) })
    return items,folders
def get_UserFolder_content( urlF,recursive=True,filtr_items={}):
    items=[]
    folders=[]
    items,folders,pagination =_scan_UserFolder(urlF,recursive,items,folders)
    if recursive:
        pagination = (False,False)
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
        print 'Filted %d items by [%s in %s]' %(cnt, value, key)
    return items,folders,pagination
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
getDuration = lambda duration: sum([a*b for a,b in zip([1,60,3600], map(int,duration.split(':')[::-1]))])
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
        print i.get('title')
        print '{"title":"%s","url":"%s","code":"%s"}' % (i.get('title'),i.get('url'),i.get('code'))
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
        link = 'https'+link
    elif link.startswith('/'):
        link = 'https://www.cda.pl'+link
    elif not link.startswith('http'):
        link=''
    return link
def grabInforFromLink(url):
    out={}
    if not 'www.cda.pl/video/' in url:
        return out
    content = getUrl(url)
    plot=re.compile('<meta property="og:description" content="(.*?)"',re.DOTALL).findall(content)
    title=re.compile('<meta property="og:title" content="(.*?)"').findall(content)
    image=re.compile('<meta property="og:image" content="(.*?)"').findall(content)
    user = re.compile('<a class="link-primary" href="(.*?)" class="autor" title="">').findall(content)
    quality=re.compile('href=".+?wersja=(.+?)"').findall(content)
    duration = re.compile('<meta itemprop=[\'"]duration[\'"] content=[\'"](.*?)[\'"]').findall(content)
    if title:
        title = PLchar(title[0])
        duration =':'.join(re.compile('(\\d+)').findall(duration[0])) if duration else ''
        duration = getDuration(duration) if duration else ''
        user = getDobryUrl(user[0])+'/folder-glowny' if user else ''
        code = quality[-1] if quality else ''
        plot = PLchar(plot[0]) if plot else ''
        img = getDobryUrlImg(image[0]) if image else ''
        out={'url':url,'title':unicode(title,'utf-8'),'code':code,'plot':unicode(plot,'utf-8'),'img':img,'duration':duration,'user':user}
    return out
import htmlentitydefs
def html_entity_decode_char(m):
    ent = m.group(1)
    if ent.startswith('x'):
        return unichr(int(ent[1:],16))
    try:
        return unichr(int(ent))
    except Exception, exception:
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
                elem = elem.get( x.decode('utf-8') )
        except:
            pass
    return elem
	
	
def jsconWalk(data,path):
    lista_katalogow = []
    lista_pozycji=[]
    
    elems = xpath(data,path) 
    if type(elems) is dict: # or type(elems) is OrderedDict:
        # created directory
        for e in elems.keys():
            one=elems.get(e)
            if type(one) is str or type(one) is unicode:    # another json file
                lista_katalogow.append( {'img':'','title':e,'url':"", "jsonfile" :one} )
            elif type(one) is dict and one.has_key('jsonfile'): # another json file v2
                one['title']=e  # dodaj tytul
                one['url']='' 
                lista_katalogow.append( one )
            else:
                if isinstance(e, unicode):
                    e = e.encode('utf8')
                elif isinstance(e, str):
                    # Must be encoded in UTF-8
                    e.decode('utf8')
                lista_katalogow.append( {'img':'','title':e,'url':path+'/'+e,'fanart':''} )
        if lista_katalogow:
             lista_katalogow= sorted(lista_katalogow, key=lambda k: (k.get('idx',''),k.get('title','')))
    if type(elems) is list:
        print 'List items'
        for one in elems:
            # check if direct link or User folder:
            if one.has_key('url'):
                lista_pozycji.append( one )
            elif one.has_key('folder'):        #This is folder in cds.pl get content:
                filtr_items = one.get('flter_item',{})
                show_subfolders = one.get('subfoders',True)
                show_items = one.get('items',True)
                is_recursive = one.get('recursive',True)
                
                items,folders,pagin = get_UserFolder_content( 
                                        urlF        = one.get('folder',''),
                                        recursive   = is_recursive,
                                        filtr_items = filtr_items )
                if show_subfolders:
                    lista_katalogow.extend(folders)
                if show_items:
                    lista_pozycji.extend(items)
                
    return (lista_pozycji,lista_katalogow)
	
	
	
	
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
                items,folders,pagination = get_UserFolder_content(
                                        urlF        = one.get('folder',''),
                                        recursive   = is_recursive,
                                        filtr_items = filtr_items )
                if show_subfolders:
                    lista_katalogow.extend(folders)
                if show_items:
                    lista_pozycji.extend(items)
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
    ids = [(a.start(), a.end()) for a in re.finditer('<span class="cover-area">', content)]
    ids.append( (-1,-1) )
    out=[]
    for i in range(len(ids[:-1])):
        item = content[ ids[i][1]:ids[i+1][0] ]
        href = re.compile('<a href="(.*?)"').findall(item)
        title= re.compile('class="kino-title">(.*?)<').findall(item)
        img = re.compile('src="(.*?)"').findall(item)
        quality = re.compile('"cloud-gray">(.*?p)<').findall(item)
        rate = re.compile('<span class="marker">(.*?)<').findall(item)
        plot = re.compile('<span class="description-cover-container">(.*?)<[/]*span',re.DOTALL).findall(item)
        if title and href:
            try:
                rating = float(rate[0]) if rate else ''
            except:
                rating = ''
            out.append({
                'title':PLchar(title[0]),
                'url':BASEURL+href[0] if not href[0].startswith('http') else href[0],
                'img':getDobryUrlImg(img[0]) if img else '',
                'code':quality[-1] if quality else '',
                'rating':rating,
                'plot':PLchar(plot[0]) if plot else ''
                })
    return out
def premium_Sort():
    return {'nowo dodane':'new',
    'alfabetycznie':'alpha',
    'najlepiej oceniane na Filmweb':'best',
    'najcz\xc4\x99\xc5\x9bciej oceniane na Filmweb':'popular',
    'data premiery kinowej':'release',
    'popularne w ci\xc4\x85gu ostatnich 60 dni':'views',
    'popularne w ci\xc4\x85gu ostatnich 30 dni':'views30'}
def qual_Sort():
    return {'Wszystkie':'1,2,3',
    'Wysoka jako\xc5\x9b\xc4\x87 (720p, 1080p)':'1',
    '\xc5\x9arednia jako\xc5\x9b\xc4\x87 (480p)':'2',
    'Niska jako\xc5\x9b\xc4\x87 (360p)':'3',
    }
def premium_Content(url,params=''):
	if len(params)==0:
		content = getUrl(url,cookies=kukz)
		out = premium_readContent(content)
		match = re.compile('katalogLoadMore\\(page,"(.*?)","(.*?)",').findall(content)
		if match:
			params = '%d_%s_%s' %(2,match[0][0],match[0][1])
	else:
		sp = params.split('_')
		myparams = str([int(sp[0]),sp[1],sp[2],{}])
		payload = '{"jsonrpc":"2.0","method":"katalogLoadMore","params":%s,"id":2}'%myparams
		content = getUrl(url.split('?')[0]+'?d=2',data=payload.replace("'",'"'),Refer=True,cookies=kukz)
		jtmp=json.loads(content).get('result') if content else {}
		if jtmp.get('status') =='continue':
			params = '%d_%s_%s' % (int(sp[0])+1,sp[1],sp[2])
		else:
			params = ''
		out = premium_readContent(jtmp.get('html',''))
	return out,params
