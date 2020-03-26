# -*- coding: utf-8 -*-

import sys,re,os
import urllib,urllib2
import urlparse
import xbmc,xbmcgui,xbmcaddon
import xbmcplugin
import json,time

try: 
	import StorageServer
except: 
	import storageserverdummy as StorageServer
cache = StorageServer.StorageServer('cda')


from resources.lib import cdapl as cda 

base_url        = sys.argv[0]
addon_handle    = int(sys.argv[1])
args            = urlparse.parse_qs(sys.argv[2][1:])
my_addon        = xbmcaddon.Addon()
my_addon_id     = my_addon.getAddonInfo('id')
PATH        = my_addon.getAddonInfo('path')
DATAPATH    = xbmc.translatePath(my_addon.getAddonInfo('profile')).decode('utf-8')
RESOURCES   = PATH+'/resources/'
MEDIA       = RESOURCES+'/media/'
FAVORITE    = os.path.join(DATAPATH,'favorites.json')
premka =  my_addon.getSetting('premka')

SERVICE     = 'cda'
if not os.path.exists(DATAPATH):
		os.makedirs(DATAPATH)
cda.COOKIEFILE  = os.path.join(DATAPATH,'cookie.cda')	

def getUrl(url,data=None):
    req = urllib2.Request(url,data)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link
	
def addLinkItem(name, url, mode, iconImage=None, infoLabels=False, contextO=['F_ADD'],IsPlayable=False,fanart=None,totalItems=1):
    u = build_url({'mode': mode, 'foldername': name, 'ex_link' : url})
    if iconImage==None:
        iconImage='DefaultFolder.png'
    if not infoLabels:
        infoLabels={'title': name}
    liz = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
    liz.setArt({ 'poster': iconImage, 'thumb' : iconImage, 'icon' : iconImage ,'fanart':fanart,'banner':iconImage})
    liz.setInfo(type='video', infoLabels=infoLabels)
    if IsPlayable:
        liz.setProperty('IsPlayable', 'True')
    if fanart:
        liz.setProperty('fanart_image',fanart)
    liz.setProperty('mimetype', 'video/x-msvideo')
    contextMenuItems = GetcontextMenuItemsXX(infoLabels,contextO,url,liz)
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz,isFolder=False,totalItems=totalItems)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED, label2Mask = '%D, %P, %R')
    return ok
	
def GetcontextMenuItemsXX(infoLabels,contextO,url,liz=None):
    contextMenuItems = []
    contextMenuItems.append(('[COLOR lightblue]Informacja[/COLOR]', 'XBMC.Action(Info)'))
    contextMenuItems.append(('[COLOR lightblue]Folder U\xc5\xbcytkownika[/COLOR]', 'XBMC.Container.Update(%s)' % build_url({'mode': 'UserContent', 'ex_link' : urllib.quote(url)})))
    content=urllib.quote_plus(json.dumps(infoLabels))
    if 'F_ADD' in contextO:
        contextMenuItems.append(('[COLOR lightblue]Dodaj do Biblioteki[/COLOR]', 'XBMC.Container.Update(plugin://%s?mode=AddMovie&ex_link=%s)'%(my_addon_id,content)))
        contextMenuItems.append(('[COLOR lightblue]Wyb\xc3\xb3r jako\xc5\x9bci [/COLOR]', 'XBMC.Container.Update(%s)'% build_url({'mode': 'decodeVideoManualQ', 'ex_link' : urllib.quote(url)})))
        contextMenuItems.append(('[COLOR lightblue]Dodaj do Wybranych[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesADD&ex_link=%s)'%(my_addon_id,content)))
    if 'F_REM' in contextO:
        contextMenuItems.append(('[COLOR red]Usu\xc5\x84 z Wybranych[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesREM&ex_link=%s)'%(my_addon_id,content)))
    if 'F_DEL' in contextO:
        contextMenuItems.append(('[COLOR red]Usu\xc5\x84 Wszystko[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesREM&ex_link=all)'%(my_addon_id)))
    if infoLabels.has_key('trailer'):
        contextMenuItems.append(('Zwiastun', 'XBMC.PlayMedia(%s)'%infoLabels.get('trailer')))
    return contextMenuItems
	
def add_Item(name, url, mode, iconImage=None, infoLabels=False, contextO=['F_ADD'],IsPlayable=False,fanart=None,totalItems=1,json_file=''):
    u = build_url({'mode': mode, 'foldername': name, 'ex_link' : url, 'json_file' : json_file})
    if iconImage==None:
        iconImage='DefaultFolder.png'
    if not infoLabels:
        infoLabels={'title': name}
    liz = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
    liz.setArt({ 'poster': iconImage, 'thumb' : iconImage, 'icon' : iconImage ,'fanart':fanart,'banner':iconImage})
    liz.setInfo(type='video', infoLabels=infoLabels)
    if IsPlayable:
        liz.setProperty('IsPlayable', 'True')
    if fanart:
        liz.setProperty('fanart_image',fanart)
    liz.setProperty('mimetype', 'video/x-msvideo')
    contextMenuItems = GetcontextMenuItemsXX(infoLabels,contextO,url)
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    return (u, liz, False)
	
def addDir(name,ex_link=None,json_file='', mode='walk',iconImage=None,fanart='',infoLabels=False,totalItems=1,contextmenu=None):
    url = build_url({'mode': mode, 'foldername': name, 'ex_link' : ex_link, 'json_file' : json_file})
    li = xbmcgui.ListItem(label=name,iconImage='DefaultFolder.png')
    if iconImage==None:
        iconImage='DefaultFolder.png'
    elif not iconImage.startswith('http'):
         iconImage = MEDIA + iconImage
    li = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
    li.setArt({ 'poster': iconImage, 'thumb' : iconImage, 'icon' : iconImage,'banner':iconImage})
    if not infoLabels:
       infoLabels={'title': name}
    li.setInfo(type='Video', infoLabels=infoLabels)
    if fanart:
        li.setProperty('fanart_image', fanart )
    if contextmenu:
        contextMenuItems=contextmenu
        li.addContextMenuItems(contextMenuItems, replaceItems=True)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_DATE, label2Mask = '%D, %P, %R')
    return ok
	
def SelSort():
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR  )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO  )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            v.decode('utf8')
        out_dict[k] = v
    return out_dict
def build_url(query):
    return base_url + '?' + urllib.urlencode(encoded_dict(query))
def drmlistitem(str_url):
	play_item=''
	from urllib import quote
	stream_url=str_url['manifest']
	PROTOCOL = 'mpd'
	DRM = 'com.widevine.alpha'
	LICENSE_URL=str_url['drm_url']
	headr = quote(str_url['drmheader'])
	import inputstreamhelper
	is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
	if is_helper.check_inputstream():
		hea = 'Content-Type=&x-dt-custom-data='+headr
		play_item = xbmcgui.ListItem(path=stream_url)
		play_item.setContentLookup(False)
		play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
		play_item.setMimeType('application/xml+dash')
		play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
		play_item.setProperty('inputstream.adaptive.license_type', DRM)

		play_item.setProperty('inputstream.adaptive.license_key', LICENSE_URL+'|' + hea+'|R{SSM}|')
	return play_item
def decodeVideo(ex_link):
   # tmp_COOKIE = cda.COOKIEFILE
   # cda.COOKIEFILE = ''
    stream_url = cda.getVideoUrls(ex_link)

    if 'drmheader' in stream_url:
		play_item = drmlistitem(stream_url)
		if play_item:
			xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
		else:
			xbmcgui.Dialog().notification('Błąd', 'Video DRM - nie udało się odtworzyć' , xbmcgui.NOTIFICATION_INFO, 5000)
			xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
    else:
        quality = my_addon.getSetting('quality')
        stream_url = selectQuality(stream_url,int(quality))
        #  cda.COOKIEFILE = tmp_COOKIE
        if 'cda.pl/video/show/' in stream_url:
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
            url = build_url({'mode': 'cdaSearch', 'ex_link' : stream_url})
            xbmc.executebuiltin('XBMC.Container.Refresh(%s)'% url)
        elif stream_url:
            xbmcplugin.setResolvedUrl(addon_handle, True, xbmcgui.ListItem(path=stream_url))
        else:
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
		
def Set_ListItem(found):
    import json
    rpccmd ={'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies', 'params': { 'filter':{'and': [{'field': 'year', 'operator': 'is', 'value': str(found.get('year',''))},{'field': 'title', 'operator': 'is', 'value': found.get('title')}]}, 'properties' :
        ['title','genre','year','plot','cast','thumbnail','art']},'id': 1}
    result = json.loads(xbmc.executeJSONRPC(json.dumps(rpccmd))).get('result',{}).get('movies',[])
    li = xbmcgui.ListItem(found.get('title',''))
    if len(result)==1:
        art =result[0].pop('art',{})
        art.update({'thumb' : result[0].get('thumbnail',''), 'icon' : result[0].get('thumbnail','')})
        caster = result[0].pop('cast',{})
        li.setArt(art)
        li.setCast(caster)
        li.setInfo('video', result[0])
    else:
        li.setInfo('video', {'year':found.get('year','')})
    return li
def playVideoRemote2(ex_link):
    found = eval(ex_link)
    tmp_COOKIE = cda.COOKIEFILE
    cda.COOKIEFILE = ''
    for href in found.get('url',[]):
        stream_url = cda.getVideoUrls(href)
        stream_url = selectQuality(stream_url,int(my_addon.getSetting('quality')))
        if not 'cda.pl/video/show/' in stream_url:
            break
    cda.COOKIEFILE = tmp_COOKIE
    if 'cda.pl/video/show/' in stream_url:
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
        url = build_url({'mode': 'cdaSearch', 'ex_link' : stream_url})
        xbmc.executebuiltin('XBMC.RunPlugin(%s)'% url)
    elif stream_url:
        li = Set_ListItem(found)
        li.setPath(path=stream_url)
        xbmcplugin.setResolvedUrl(addon_handle, True, li)
    else:
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
def selectQuality(stream_url,quality):
    msg = u'Wybierz jako\u015b\u0107 video [albo ustaw automat w opcjach]'
    vid_url=''
    if type(stream_url) is list:
        qualityList = [x[0] for x in stream_url]
        if quality > 0:
            user_selection = ['','Najlepsza','1080p','720p','480p','360p'][quality]
            if user_selection=='Najlepsza' and stream_url[0][1]:
                vid_url = cda.getVideoUrls(stream_url[0][1],4)
            elif user_selection in qualityList:
                vid_url = cda.getVideoUrls(stream_url[qualityList.index(user_selection)][1],4)
            else:
                msg = u'Problem z automatycznym wyborem ... wybierz jako\u015b\u0107'
        if not vid_url:
            if len(stream_url)==1 and stream_url[0][1]=='':
                msg=u'[COLOR red]%s[/COLOR]\n'%(unicode(stream_url[0][0],'utf-8'))
                title = cda.replacePLch(fname.split('[')[0])
                yes = xbmcgui.Dialog().yesno('[COLOR red]Problem[/COLOR]',msg+u'Problem do [COLOR lightblue]%s[/COLOR]'%title,'Szukaj nowego \xc5\xbar\xc3\xb3d\xc5\x82a?')
                if yes:
                    vid_url='https://www.cda.pl/video/show/'+cda.replacePLch(title.replace(' ','_'))
            else:
                selection = xbmcgui.Dialog().select(msg, qualityList)
                if selection>-1:
                    vid_url = cda.getVideoUrls(stream_url[selection][1],4)
                    if isinstance(vid_url,list):
                        vid_url=''
                else:
                    vid_url=''
    else:
        vid_url = stream_url
    return vid_url
def playVideoRemote(ex_link,wart=1):
    stream_url = cda.getVideoUrls(ex_link)
    quality = my_addon.getSetting('quality_remote')
    stream_url = selectQuality(stream_url,int(quality)*wart)
    if not stream_url:
        return False
    out = cda.grabInforFromLink(ex_link)
    if not out:
        out['title']='Remote video'
    liz=xbmcgui.ListItem(out.get('title'), iconImage=out.get('img','DefaultVideo.png'))
    liz.setInfo( type='Video', infoLabels=out)
    try:
        Player = xbmc.Player()
        Player.play(stream_url, liz)
    except Exception as ex:
        xbmcgui.Dialog().ok('Problem z odtworzeniem.', 'Wyst\xc4\x85pi\xc5\x82 nieznany b\xc5\x82\xc4\x85d', str(ex))
    return 1
def userFolderADD():
    folder_list=[]
    for userF in ['K1','K2','K3','K4','K5','K6']:
        one = userFolder(userF)
        if one:
            addDir(one.get('title'),ex_link=one.get('url'), mode='cdaSearch', json_file=one.get('metadata'),iconImage='Szukaj_cda.png')
def userFolder(userF='K1'):
    enabled = my_addon.getSetting(userF)
    if enabled=='true':
        title = my_addon.getSetting(userF+'_filtr0')
        list_of_special_chars = [
        ('Ą', b'a'),('ą', b'a'),('Ę', b'e'),('ę', b'e'),('Ó', b'o'),('ó', b'o'),('Ć', b'c'),
        ('ć', b'c'),('Ł', b'l'),('ł', b'l'),('Ń', b'n'),('ń', b'n'),('Ś', b's'),('ś', b's'),
        ('Ź', b'z'),('ź', b'z'),('Ż', b'z'),('ż', b'z'),(' ','_')]
        title =  my_addon.getSetting(userF+'_title')
        if not title:
            title = title.title()
        for a,b in list_of_special_chars:
            title = title.replace(a,b)
        title = title.lower()
        sel = my_addon.getSetting(userF+'_filtr1')
        dlugoscL = ['all','krotkie','srednie','dlugie']
        dlugosc = dlugoscL[int(sel)]
        sel = my_addon.getSetting(userF+'_filtr2')
        jakoscL = ['all','480p','720p','1080p']
        jakosc= jakoscL[int(sel)]
        sel = my_addon.getSetting(userF+'_filtr3')
        sortujL=['best','date','popular','rate','alf']
        sortuj=sortujL[int(sel)]
        filmweb = my_addon.getSetting(userF+'_fwmeta')
        url='https://www.cda.pl/video/show/%s?duration=%s&section=vid&quality=%s&section=&s=%s&section='%(title,dlugosc,jakosc,sortuj)
        return {'url':url,'title': '[COLOR lightblue]%s[/COLOR]'%title,'metadata':filmweb }
    return False
def get_Root():
    out={}
    jsRootFile="https://pastebin.com/raw/Ei8sWMfW"
    if jsRootFile: out['[COLOR white][B]Root[/B][/COLOR]']= {'jsonfile':jsRootFile,'img':'Media.png'}
    else : out['[COLOR red][B]Quota Exceeded[/B][/COLOR]']= {'jsonfile':jsRootFile,'img':'Media.png'}
    return out
	
def encoded_v(v):
    if isinstance(v, unicode): v = v.encode('utf8')
    elif isinstance(v, str): v.decode('utf8')
    return v
	
def updateMetadata(item):
    from resources.lib import filmwebapi as fa #import filmwebapi as fa
    tytul = item.get('title')
    title,year,label=cda.cleanTitle(tytul)
    data = fa.searchFilmweb2(title.strip(),year.strip())
    if data:
        data['date']=None
        item.update(data)
        item['OriginalTitle']=tytul
        item['_filmweb']=item.get('filmweb',False)
        if label: item['label']=label
        item['title'] += ' (%s) %s'%(item.get('year',''),item.get('label','')) + item.get('msg','')
    else:
        pass
    return item
	
def mainWalk(ex_link='',json_file='',fname=''):
    items=[]
    folders=[]
    contextmenu=[]
    pagination=(False,False)
    if ex_link=='' or ex_link.startswith('/'):
	
        data = cda.ReadJsonFile(json_file) if json_file else get_Root()
        items,folders = cda.jsconWalk(data,ex_link)
    if 'folder' in ex_link or 'ulubione' in ex_link:
        recursive = False if my_addon.getSetting('UserFolder.content.paginatoin')=='true' else True
        items,folders,pagination = cda.get_UserFolder_content(
                                urlF        = ex_link,
                                recursive   = recursive,
                                filtr_items = {} )
    elif 'obserwowani' in ex_link:
        items,folders = cda.get_UserFolder_obserwowani(ex_link)
    if pagination[0]:
        addLinkItem('[COLOR gold] << Poprzednia strona [/COLOR]', url=pagination[1], mode='__page:walk', iconImage='prev.png', infoLabels=False, contextO=[],IsPlayable=False,fanart=None,totalItems=1)
    N_folders=len(items)
    for f in folders:
        tmp_json_file = f.get('jsonfile',json_file)
        title = f.get('title') + f.get('count','')
        f['plot'] = f.get('plot','') + '\n' + f.get('update','')
        if f.get('lib',False):
            contextmenu = [('[COLOR lightblue]Dodaj zawarto\xc5\x9b\xc4\x87 do Biblioteki[/COLOR]', 'RunPlugin(plugin://%s?mode=AddRootFolder&json_file=%s)'%(my_addon_id,urllib.quote_plus(tmp_json_file)))]
        else:
            contextmenu = []
        addDir(title,ex_link=f.get('url'), json_file=tmp_json_file, mode='walk', iconImage=f.get('img',''),infoLabels=f,fanart=f.get('fanart',''),contextmenu=contextmenu,totalItems=N_folders)
    contextO=['F_ADD']
    if fname=='[COLOR khaki]Wybrane[/COLOR]':
        contextO=['F_REM','F_DEL']
    N_items=len(items)
    list_of_items=[]
    for item in items:
        list_of_items.append( add_Item(name=item.get('title').encode('utf-8'), url=item.get('url'), mode='decodeVideo',contextO=contextO, iconImage=item.get('img'), infoLabels=item, IsPlayable=True,fanart=item.get('img')) )
    xbmcplugin.addDirectoryItems(handle=addon_handle, items = list_of_items ,totalItems=N_items)
    if pagination[1]:
        addLinkItem('[COLOR gold]Nast\xc4\x99pna strona >> [/COLOR] ', url=pagination[1], mode='__page:walk', iconImage='next.png', infoLabels=False, contextO=[],IsPlayable=False,fanart=None,totalItems=1)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED, label2Mask = '%D, %P, %R')
    SelSort()
    return 1
def cdaSearch(ex_link):
    use_filmweb = json_file if json_file else my_addon.getSetting('filmweb_search')
    use_premium =True if my_addon.getSetting('search_premium')=='true' else False
    use_premium = False if use_filmweb=='true' else use_premium
    bcleanTitle =True if my_addon.getSetting('bcleanTitle')=='true' else False
    if use_filmweb=='true':
        bcleanTitle = False
    items,nextpage = cda.searchCDA(ex_link,use_premium,bcleanTitle)
    N_items=len(items)
    xbmc.log(' N_items %d'%N_items)
    if use_filmweb=='true' and len(items)>0:
        xbmc.log(' WorkerThreadPool ')
        from resources.lib import thread_pool
        pool = thread_pool.ThreadPool(15)
        xbmc.log('  pool.map(updateMetadata, items) ')
        pool.map(updateMetadata, items)
        pool.wait_completion()
        xbmc.log('  wait_completion DONE')
    if items:
        for item in items:
            addLinkItem(name=item.get('title').encode('utf-8'), url=item.get('url'), mode='decodeVideo', iconImage=item.get('img'), infoLabels=item, IsPlayable=True,fanart=item.get('img'),totalItems=N_items)
        if nextpage:
            addDir('[COLOR gold]Nast\xc4\x99pna strona >> [/COLOR] ',ex_link=nextpage, json_file=use_filmweb, mode='cdaSearch',iconImage='next.png')
    SelSort()
    x=xbmcplugin.endOfDirectory(addon_handle,succeeded=True)
def logincda():
	u = my_addon.getSetting('user')
	p = my_addon.getSetting('pass')
	if u and p:
		logged,typ = cda.CDA_login(u,p,DATAPATH+'cookie.cda')
		if logged:
			plot = 'Konto darmowe'
			if typ:
				plot = 'Konto premium'
			cda.COOKIEFILE=DATAPATH+'cookie.cda'
			addDir('[B]Moje cda.pl[/B]',ex_link='', json_file='', mode='MojeCDA', iconImage='cdaMoje.png',infoLabels={'plot':plot})


def HistoryLoad():
    return cache.get('history').split(';')
dekodowanie = lambda (t) : t.encode('utf-8') if isinstance(t,unicode) else t
def HistoryAdd(entry):
	history = HistoryLoad()
	if history == ['']:
		history = []
	
	
	
	
	history.insert(0, dekodowanie(entry))
	try:
		cache.set('history',';'.join(history[:50]))
	except:
		pass
def HistoryDel(entry):
    history = HistoryLoad()
    if history:
        cache.set('history',';'.join(history[:50]))
    else:
        HistoryClear()
def HistoryClear():
    cache.delete('history')
xbmcplugin.setContent(addon_handle, 'movies')
mode = args.get('mode', None)
fname = args.get('foldername',[''])[0]
ex_link = args.get('ex_link',[''])[0]
json_file = args.get('json_file',[''])[0]
if mode is None:
    logincda()
    mainWalk()
    addDir('[COLOR white][B]Filmy Premium[/B][/COLOR]',ex_link='', mode='premiumKat',iconImage='MediaPremium.png')
    userFolderADD()
    addDir('Wybrane',ex_link='', json_file=FAVORITE, mode='walk',  iconImage='cdaUlubione.png',infoLabels={'plot':'Lista wybranych pozycji. Szybki dostep, lokalna baza danych.'})
    addDir('Szukaj',ex_link='', mode='Szukaj',iconImage='Szukaj_cda.png')
    if my_addon.getSetting('library.mainmenu') == 'true':
        addDir('-=Biblioteka=-','','','Library',iconImage='library.png')
    addLinkItem('-=Opcje=-','','Opcje',iconImage=MEDIA+'Opcje.png')
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True)
elif mode[0] == 'Library':
    from resources.lib import libtools
    lib_mov = libtools.libmovies()
    addLinkItem(lib_mov.service_online,'','',iconImage=MEDIA+'Opcje.png',infoLabels={'plot':'Serwis mo\xc5\xbce wymaga\xc4\x87 ponownego uruchomienia KODI je\xc5\x9bli zosta\xc5\x82 w\xc5\x82\xc4\x85czony lub wy\xc5\x82aczony po raz pierwszy.'})
    addLinkItem(lib_mov.ilosc_filmow,'','',iconImage=MEDIA+'Opcje.png',infoLabels={'plot':'Ilo\xc5\x9b\xc4\x87 pozycji w bibliotece. Faktyczna liczba mo\xc5\xbce si\xc4\x99 ro\xc5\xbcni\xc4\x87 je\xc5\x9bli movie srapper nie rozpozna\xc5\x82 filmu. Zaleca si\xc4\x99 u\xc5\xbcywanie Filmweb scrappera z Regss repozytorium.'})
    addLinkItem(lib_mov.ostat_aktualizacja,'','',iconImage=MEDIA+'Opcje.png')
    addLinkItem(lib_mov.aktualizacja_co_ile,'','',iconImage=MEDIA+'Opcje.png')
    addLinkItem(lib_mov.nie_sa_sprawdzane,'','',iconImage=MEDIA+'Opcje.png')
    addLinkItem(lib_mov.nast_szukanie,'','',iconImage=MEDIA+'Opcje.png')
    addLinkItem('[B][Szukaj nowych film\xc3\xb3w][/B]','','GetNewMovies',iconImage=MEDIA+'library.png',infoLabels={'plot':'Metoda przeszukuje [B]X[/B] pierwszych stron z filmami w serwisie cda.pl w poszukuwaniu nowych pozycji.\n\nR\xc4\x99czne uruchomienie jednej akcji serwisu.'})
    addLinkItem('[B][Sprawd\xc5\xba \xc5\xbar\xc3\xb3d\xc5\x82a film\xc3\xb3w][/B]','','CheckLinksInLibrary',iconImage=MEDIA+'library.png',infoLabels={'plot':'Metoda sprawdza czy \xc5\xbar\xc3\xb3d\xc5\x82a w bibliotece s\xc4\x85 jeszcze aktulane. Ka\xc5\xbcda pozycja jest indywidualnie testowana raz na [B]X[/B] dni.\n\nR\xc4\x99czne uruchomienie jednej akcji serwisu.'})
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True)
elif mode[0].startswith('_info_'):
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0].startswith('__page'):
    my_mode=mode[0].split(':')[-1]
    url = build_url({'mode': my_mode, 'foldername': fname, 'ex_link' : ex_link, 'json_file' : json_file})
    xbmc.executebuiltin('XBMC.Container.Refresh(%s)'% url)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True)
elif mode[0] == 'premiumKat':
    try:
        folders=cda.premium_Katagorie()
    except:folders=[]
    sortuj_po = my_addon.getSetting('sortuj_po')
    jakosc_premium = my_addon.getSetting('jakosc_premium')
    N_folders=len(folders)+2
    addDir(' [COLOR white]== Sortuj po: [I]%s[/I] [/COLOR]'%sortuj_po, ex_link='', json_file='', mode='premiumSort', iconImage='',totalItems=N_folders)
    addDir(' [COLOR white]== Jako\xc5\x9b\xc4\x87: [I]%s[/I] [/COLOR]'%jakosc_premium, ex_link='', json_file='', mode='premiumQuality', iconImage='',totalItems=N_folders)
    for f in folders:
        addDir(f.get('title'),ex_link=f.get('url'), json_file='', mode='premiumFilm', iconImage=f.get('img',''),infoLabels=f,fanart=f.get('fanart',''),totalItems=N_folders)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] == 'premiumSort':
    sortuj= cda.premium_Sort()
    selection = xbmcgui.Dialog().select('Sortuj po:', sortuj.keys())
    if selection>-1:
        my_sort= sortuj.keys()[selection]
        my_addon.setSetting('sortuj_po',my_sort)
        xbmc.executebuiltin('XBMC.Container.Refresh')
elif mode[0] == 'premiumQuality':
    sortuj= cda.qual_Sort()
    selection = xbmcgui.Dialog().select('Jako\xc5\x9b\xc4\x87:', sortuj.keys())
    if selection>-1:
        my_sort= sortuj.keys()[selection]
        my_addon.setSetting('jakosc_premium',my_sort)
        xbmc.executebuiltin('XBMC.Container.Refresh')
elif mode[0] == 'premiumFilm':
	sortuj_po = my_addon.getSetting('sortuj_po')
	jakosc_premium = my_addon.getSetting('jakosc_premium')
	if '?' not in ex_link:
		url = ex_link+'?sort=%s&q=%s&d=2'%(cda.premium_Sort().get(sortuj_po,''),cda.qual_Sort().get(jakosc_premium,''))
		if premka=='true':
			url = ex_link+'?sort=%s&q=%s&d=1,2'%(cda.premium_Sort().get(sortuj_po,''),cda.qual_Sort().get(jakosc_premium,''))
	else:
		url = ex_link
	items,params=cda.premium_Content(url,json_file)
	for item in items:
		name= cda.html_entity_decode(item.get('title',''))
		href = item.get('url','')
		if 'folder' in href:
			addDir(name,ex_link=href, json_file='ignore', mode='walk',infoLabels=item,iconImage=item.get('img'))
		else:
			addLinkItem(name=name, url=href, mode='decodeVideo',contextO=[], iconImage=item.get('img'), infoLabels=item, IsPlayable=True,fanart=item.get('img'),totalItems=len(items))
	if params:
		addDir('[COLOR gold]Nast\xc4\x99pna strona >> [/COLOR] ',ex_link=url, json_file=params, mode='premiumFilm',iconImage='next.png')
	xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] == 'favoritesADD':
    jdata = cda.ReadJsonFile(FAVORITE)
    new_item=json.loads(ex_link)
    new_item['title'] = new_item.get('title','').replace(new_item.get('label',''),'').replace(new_item.get('msg',''),'')
    dodac = [x for x in jdata if new_item['title']== x.get('title','')]
    if dodac:
        xbmc.executebuiltin('Notification([COLOR pink]Ju\xc5\xbc jest w Wybranych[/COLOR], ' + new_item.get('title','').encode('utf-8') + ', 200)')
    else:
        jdata.append(new_item)
        with open(FAVORITE, 'w') as outfile:
            json.dump(jdata, outfile, indent=2, sort_keys=True)
            xbmc.executebuiltin('Notification(Dodano Do Wybranych, ' + new_item.get('title','').encode('utf-8') + ', 200)')
elif mode[0] == 'favoritesREM':
    if ex_link=='all':
        yes = xbmcgui.Dialog().yesno('??','Usu\xc5\x84 wszystkie filmy z Wybranych?')
        if yes:
            debug=1
    else:
        jdata = cda.ReadJsonFile(FAVORITE)
        remItem=json.loads(ex_link)
        to_remove=[]
        for i in xrange(len(jdata)):
            if jdata[i].get('title') in remItem.get('title'):
                to_remove.append(i)
        if len(to_remove)>1:
            yes = xbmcgui.Dialog().yesno('??',remItem.get('title'),'Usu\xc5\x84 %d pozycji z Wybranych?' % len(to_remove))
        else:
            yes = True
        if yes:
            for i in reversed(to_remove):
                jdata.pop(i)
            with open(FAVORITE, 'w') as outfile:
                json.dump(jdata, outfile, indent=2, sort_keys=True)
    xbmc.executebuiltin('XBMC.Container.Refresh')
elif mode[0]=='cdaSearch':
    cdaSearch(ex_link)
elif mode[0] =='Szukaj':
    addDir('[COLOR lightblue]Nowe Szukanie[/COLOR]','',mode='SzukajNowe')
    historia = HistoryLoad()
    if not historia == ['']:
        for entry in historia:
            contextmenu = []
            contextmenu.append(('Usu\xc5\x84', 'XBMC.Container.Update(%s)'% build_url({'mode': 'SzukajUsun', 'ex_link' : entry})),)
            contextmenu.append(('Usu\xc5\x84 ca\xc5\x82\xc4\x85 histori\xc4\x99', 'XBMC.Container.Update(%s)' % build_url({'mode': 'SzukajUsunAll'})),)
            addDir(name=entry, ex_link='http://www.cda.pl/video/show/'+entry.replace(' ','_'), mode='cdaSearch', fanart=None, contextmenu=contextmenu)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] =='SzukajNowe':
    d = xbmcgui.Dialog().input('Szukaj, podaj tytu\xc5\x82', type=xbmcgui.INPUT_ALPHANUM)
    if d:
        HistoryAdd(d)
        ex_link='https://www.cda.pl/video/show/'+d.replace(' ','_')
        cdaSearch(ex_link)
elif mode[0] =='SzukajUsun':
    HistoryDel(ex_link)
    xbmc.executebuiltin('XBMC.Container.Refresh(%s)'%  build_url({'mode': 'Szukaj'}))
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] == 'SzukajUsunAll':
    HistoryClear()
    xbmc.executebuiltin('XBMC.Container.Refresh(%s)'%  build_url({'mode': 'Szukaj'}))
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] == 'MojeCDA':
    u = my_addon.getSetting('user')
    if u:
        addDir('Folder g\xc5\x82\xc3\xb3wny',ex_link='https://www.cda.pl/'+u+'/folder-glowny?type=pliki', json_file='', mode='walk', iconImage='cdaMoje.png')
        addDir('Ulubione',ex_link='https://www.cda.pl/'+u+'/ulubione/folder-glowny?type=pliki', json_file='', mode='walk', iconImage='cdaUlubione.png')
        addDir('Obserwowani u\xc5\xbcytkownicy',ex_link='https://www.cda.pl/'+u+'/obserwowani', json_file='', mode='walk', iconImage='cdaObserwowani.png')
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True)
elif mode[0] == 'decodeVideo':
    decodeVideo(ex_link)
elif mode[0] == 'decodeVideoManualQ':
    playVideoRemote(ex_link,wart=0)
elif mode[0] == 'play':
    xbmcgui.Dialog().notification('Remote video requested', ex_link , xbmcgui.NOTIFICATION_INFO, 5000)
    playVideoRemote(ex_link)
elif mode[0] == 'Opcje':
    my_addon.openSettings()
    xbmc.executebuiltin('XBMC.Container.Refresh()')
elif mode[0] == 'UserContent':
    info = cda.grabInforFromLink(urllib.unquote(ex_link))
    user =info.get('user','')
    if user:
        mainWalk(user,'','')
        xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
    else:
        xbmcgui.Dialog().notification('Folder nie jest dost\xc4\x99pny', '' , xbmcgui.NOTIFICATION_INFO, 5000)
elif mode[0] =='AddMovie':
    from resources.lib import libtools
    new_item=json.loads(ex_link)
    if not new_item.get('_filmweb',False):
        title,year,label=cda.cleanTitle(new_item.get('title'))
        quer = xbmcgui.Dialog().input('Tytu\xc5\x82_Filmu Rok (popraw je\xc5\x9bli trzeba)', '%s %s'%(title,year) ,xbmcgui.INPUT_ALPHANUM)
        new_item['title']=quer.decode('utf-8')
        xbmcgui.Dialog().notification('Sprawdzam video', new_item['title'] , new_item.get('img',xbmcgui.NOTIFICATION_INFO), 5000)
        new_item = updateMetadata(new_item)
    new_item['title']=new_item.get('title','').split('[COLOR')[0]
    if new_item.get('_filmweb',False):
        libtools.libmoviesOk().add(new_item)
    else:
        xbmcgui.Dialog().notification('Nic nie dodanoo', new_item.get('title','') , new_item.get('img',xbmcgui.NOTIFICATION_INFO), 5000)
elif mode[0] =='AddRootFolder':
    from resources.lib import libtools
    i = cda.ReadJsonFile(json_file)
    libtools.libmoviesOk().add2(i)
elif mode[0] == 'GetNewMovies':
    from resources.lib import libtools
    libtools.libmoviesOk().GetNewMovies()
elif mode[0] == 'CheckLinksInLibrary':
    from resources.lib import libtools
    libtools.libmoviesOk().CheckLinksInLibrary()
elif mode[0] == 'lplay':
    playVideoRemote2(ex_link)
elif mode[0] == 'walk':
    mainWalk(ex_link,json_file,fname)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,cacheToDisc=False)
elif mode[0] == 'folder':
    pass


