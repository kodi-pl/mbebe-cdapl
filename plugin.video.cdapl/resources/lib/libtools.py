# -*- coding: utf-8 -*-

import datetime
import json
import os
import re
import sys
import urllib
import urllib2
import urlparse
import xbmc
import control #control
import re
import unicodedata

def cleantitle(title):
    try:
        title = replacePLch(title)
        try: return title.decode('ascii').encode('utf-8')
        except: pass
        return str(''.join(c for c in unicodedata.normalize('NFKD', unicode(title.decode('utf-8'))) if unicodedata.category(c) != 'Mn'))
    except:
        return title
		
def replacePLch(itemF):
    list_of_special_chars = [
    ('\xc4\x84', 'a'),('\xc4\x85', 'a'),('\xc4\x98', 'e'),('\xc4\x99', 'e'),('\xc3\x93', 'o'),('\xc3\xb3', 'o'),('\xc4\x86', 'c'),
    ('\xc4\x87', 'c'),('\xc5\x81', 'l'),('\xc5\x82', 'l'),('\xc5\x83', 'n'),('\xc5\x84', 'n'),('\xc5\x9a', 's'),('\xc5\x9b', 's'),
    ('\xc5\xb9', 'z'),('\xc5\xba', 'z'),('\xc5\xbb', 'z'),('\xc5\xbc', 'z')]
    for a,b in list_of_special_chars:
        itemF = itemF.replace(a,b)
    return itemF
	
def printuj_linka(itemF=''):
    print '[CDA.PL Library]: %s'%itemF
	
class lib_tools:
    @staticmethod
    def create_folder(folder):
        try:
            folder = xbmc.makeLegalFilename(folder)
            control.makeFile(folder)
            try:
                if not 'ftp://' in folder: raise Exception()
                from ftplib import FTP
                ftparg = re.compile('ftp://(.+?):(.+?)@(.+?):?(\\d+)?/(.+/?)').findall(folder)
                ftp = FTP(ftparg[0][2], ftparg[0][0], ftparg[0][1])
                try:
                    ftp.cwd(ftparg[0][4])
                except:
                    ftp.mkd(ftparg[0][4])
                ftp.quit()
            except:
                pass
        except:
            pass
			
    @staticmethod
    def write_file(path, content):
        try:
            path = xbmc.makeLegalFilename(path)
            if not isinstance(content, basestring):
                content = str(content)
            file = control.openFile(path, 'w')
            file.write(str(content))
            file.close()
        except Exception as e:
            pass
			
    @staticmethod
    def write_file2(path):
        content = None
        try:
            path = xbmc.makeLegalFilename(path)
            file = control.openFile(path, 'r')
            content = file.read()
            file.close()
        except Exception as e:
            pass
        return content
		
    @staticmethod
    def nfo_url(media_string, ids):
        tvdb_url = 'http://thetvdb.com/?tab=series&id=%s'
        tmdb_url = 'https://www.themoviedb.org/%s/%s'
        imdb_url = 'http://www.imdb.com/title/%s/'
        filmweb1_url= 'http://www.filmweb.pl%s'
        filmweb2_url ='http://www.filmweb.pl/Film?id=%s'
        if 'tvdb' in ids:
            return tvdb_url % (str(ids['tvdb']))
        elif 'tmdb' in ids:
            return tmdb_url % (media_string, str(ids['tmdb']))
        elif 'imdb' in ids:
            return imdb_url % (str(ids['imdb']))
        elif 'data_film' in ids:
            return filmweb2_url % (str(ids['data_film']))
        elif 'filmwebhref' in ids:
            return filmweb1_url % (str(ids['filmwebhref']))
        else:
            return ''
			
    @staticmethod
    def check_sources(title, year, imdb, tvdb=None, season=None, episode=None, tvshowtitle=None, premiered=None):
        return True
		
    @staticmethod
    def legal_filename(filename):
        try:
            filename = filename.strip()
            filename = re.sub('(?!%s)[^\\w\\-_\\.]', '.', filename)
            filename = re.sub('\\.+', '.', filename)
            filename = re.sub(re.compile('(CON|PRN|AUX|NUL|COM\\d|LPT\\d)\\.', re.I), '\\1_', filename)
            xbmc.makeLegalFilename(filename)
            return filename
        except:
            return filename
			
    @staticmethod
    def make_path(base_path, title, year='', season=''):
        show_folder = re.sub('[^\\w\\-_\\. ]', '_', title)
        show_folder = '%s (%s)' % (show_folder, year) if year else show_folder
        path = os.path.join(base_path, show_folder)
        if season:
            path = os.path.join(path, 'Season %s' % season)
        return path
		
    @staticmethod
    def get_urlStat(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36')
        response = 'NotChecked'
        try:
            resp = urllib2.urlopen(req)
            response='OK'
        except urllib2.HTTPError, e:
            response = 'HTTPError = ' + str(e.code)
        except urllib2.URLError, e:
            response =  'URLError = ' + str(e.reason)
        except httplib.HTTPException, e:
            response = 'HTTPException'
        return response
		
    @staticmethod
    def encoded_v(v):
        if isinstance(v, unicode): v = v.encode('utf8')
        elif isinstance(v, str): v.decode('utf8')
        return v
		
    @staticmethod
    def build_url(query):
        def encoded_dict(in_dict):
            out_dict = {}
            for k, v in in_dict.items():
                if isinstance(v, unicode): v = v.encode('utf8')
                elif isinstance(v, str): v.decode('utf8')
                out_dict[k] = v
            return out_dict
        addonID_ = 'plugin://plugin.video.cdapl/'
        return addonID_ + '?' + urllib.urlencode(encoded_dict(query))
		
class libmovies:
    def __init__(self):
        self.library_folder = os.path.join(control.transPath(control.setting('library.movie')), '')
        try:
            lib_serv_last_run = control.setting('library.service.last.run')
            lib_serv_last_run = datetime.datetime.strptime(lib_serv_last_run, '%Y-%m-%d %H:%M:%S')
            t1 = datetime.timedelta(hours=int(control.setting('library.service.wait.time')))
            czasOK = t1-abs(datetime.datetime.now() - lib_serv_last_run)
        except:
            czasOK= False
        dirs,files = control.listDir(self.library_folder) if self.library_folder else ([],[])
        self.ilosc_filmow = 'Ilo\xc5\x9b\xc4\x87 film\xc3\xb3w w bibliotece: [B]%d[/B]'%len(dirs)
        self.aktualizacja_co_ile = 'Aktulizacja co: [B]%s h[/B]'%control.setting('library.service.wait.time')
        lib_serv_test_delay = control.setting('library.service.testlink.delay')
        self.nie_sa_sprawdzane = '\xc5\xb9r\xc3\xb3d\xc5\x82a biblioteki nie s\xc4\x85 sprawdzane okresowo [B](0 dni)[/B]' if lib_serv_test_delay=='0' else 'Sprawdzanie \xc5\xbar\xc3\xb3de\xc5\x82 co: [B]%s dni[/B]'%lib_serv_test_delay
        self.service_online = 'Service: [COLOR lightgreen]online[/COLOR]' if control.setting('library.service.active') == 'true' else 'Service: [COLOR red]offline[/COLOR]'
        if control.setting('library.service.active') == 'true' and czasOK:
            chwilka = 'chwilk\xc4\x99' if czasOK.days<0 else str(czasOK).split('.')[0]+' h'
            self.nast_szukanie = 'Nast\xc4\x99pne szukanie za ok: [B] %s [/B] '%chwilka
        else:
            self.nast_szukanie = 'Nast\xc4\x99pne szukanie nie wiadomo kiedy'
        self.ostat_aktualizacja = 'Ostatnia Aktualizacja: [B]%s[/B]'%control.setting('library.service.last.run')

class libmoviesOk:
    def __init__(self):
        self.library_folder = os.path.join(control.transPath(control.setting('library.movie')), '')
        self.check_setting = control.setting('library.check_movie') or 'false'
        self.library_setting = control.setting('library.update') or 'true'
        self.dupe_setting = control.setting('library.check') or 'true'
        self.fredy = 10
        self.infoDialog = False
        self.silentDialog = False
        self.war1 = True
		
    def add(self, found):
        fwebId = found.get('_filmweb',False)
        title = found.get('title','')
        title = re.sub('\\(\\d{4}\\)','',title).strip()
        year  = found.get('year','')
        url   = found.get('url','')
        if not ( fwebId and url):
            return False
        if self.check_setting == 'true':
            if lib_tools.get_urlStat(url) != 'OK':
                return False
        if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
            control.infoDialog('Dodawanie do Biblioteki ...', time=3)
            self.infoDialog = True
        files_added = 0
        if self.strmFile(fwebId,title,year,url):
            files_added += 1
        if self.infoDialog == True:
            control.infoDialog('Zako\xc5\x84czono', time=2)
        if self.library_setting == 'true' and not control.condVisibility('Library.IsScanningVideo') and files_added > 0:
            control.execute('UpdateLibrary(video)')
			
    def add2(self, i):
        if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
            try:
                control.infoDialog('Dodawanie Folderu do Biblioteki ...', time=3)
                self.infoDialog = True
            except:
                self.infoDialog = False
        files_added = 0
        progressDialogBG = control.progressDialogBG
        progressDialogBG.create('cda.pl','Dodawanie Folderu do Biblioteki')
        for index, found in enumerate(i):
            czas_progres = int((index+1)*100.0/(len(i)))
            fwebId = found.get('_filmweb',False)
            title = found.get('title','')
            title = re.sub('\\(\\d{4}\\)','',title).strip()
            year  = found.get('year','')
            url   = found.get('url','')
            if not ( fwebId and url): continue
            if self.check_setting == 'true':
                if lib_tools.get_urlStat(url) != 'OK':
                    progressDialogBG.update(czas_progres,message='martwy link [%s] '%(title))
                    printuj_linka('[CheckLink]: BAD Source: %s'%title)
                    continue
                else:
                    printuj_linka('[CheckLink]: OK Source: %s'%title)
            if self.strmFile(fwebId,title,year,url):
                files_added += 1
                progressDialogBG.update(czas_progres,message='Dodano [%s] '%(title))
        progressDialogBG.close()
        if self.infoDialog == True:
            control.infoDialog('Dodano %d film\xc3\xb3w'%files_added, time=2)
        if self.library_setting == 'true' and not control.condVisibility('Library.IsScanningVideo') and files_added > 0:
            control.execute('UpdateLibrary(video)')
			
    def strmFile(self, fwebId, title, year, url):
        if isinstance(title,unicode): title = title.encode('utf-8')
        transtitle = cleantitle(title.translate(None, '\\/:*?"<>|') )
        content = lib_tools.build_url({'mode': 'lplay', 'ex_link':str({'_filmweb':fwebId,'title':title,'year':year,'url':[url],'linkchecked': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') })})
        folder = lib_tools.make_path(self.library_folder, transtitle, year)
        lib_tools.create_folder(folder)
        sciezka1 = os.path.join(folder, lib_tools.legal_filename(transtitle) + '.strm')
        if self.war1 == True and os.path.exists(sciezka1):
            content = lib_tools.write_file2(sciezka1)
            hrefOut = eval(urlparse.parse_qs(content.split('?')[-1]).get('ex_link',{})[0]).get('url',[])
            hrefOut.append(url)
            hrefOut = list(set(hrefOut))
            content = lib_tools.build_url({'mode': 'lplay', 'ex_link':str({'_filmweb':fwebId,'title':title,'year':year,'url':hrefOut,'linkchecked': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') })})
        lib_tools.write_file(sciezka1, content)
        lib_tools.write_file(os.path.join(folder, 'movie.nfo'), lib_tools.nfo_url('movie', {'data_film':fwebId}))
        ok = True
        return ok
		
    def dod_Movies(self,one,idx,N):
        from cdapl import cleanTitle
        from filmwebapi import searchFilmweb3
        title, year, label = cleanTitle(one.get('title'))
        title = title.split('-')[0]
        title = lib_tools.encoded_v(title)
        rok = year or one.get('year')
        czas_progres = int((idx+1)*100.0/(N))
        found = searchFilmweb3(title,rok)
        if found:
            printuj_linka('[AddMovie]: Movie -> %s (%s) '%(found.get('title'),found.get('year')))
            found['_filmweb']=found.get('id','')
            found['url']= one.get('url')
            self.out.append(found)
            self.progressDialogBG.update(czas_progres,message='%s (%s)'%(found.get('title'),found.get('year')))
			
    def GetNewMovies(self):
        from cdapl import searchCDA
        import thread_pool
        import time
        self.check_setting = 'false'
        url = 'https://www.cda.pl/video/show/cale_filmy_or_caly_film_or_lektor_or_pl_or_dubbing_or_napisy_or_fps_or_odc/p%d?duration=dlugie&section=&quality=720p&section=&s=date&section='
        if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
            try:
                control.infoDialog('Szukam nowych film\xc3\xb3w ...', time=3)
                self.infoDialog = True
            except:
                self.infoDialog = False
        self.progressDialogBG = control.progressDialogBG
        self.progressDialogBG.create('cda.pl','Szukam nowych film\xc3\xb3w ...')
        items=[]
        control.setSetting('library.service.last.run', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for stronkaX in range(int(control.setting('library.service.pages') or 1)):
            stronkaX +=1
            printuj_linka('[AddMovie]: Searching cda.pl, page [%d]'%stronkaX)
            nowy_link,next=searchCDA(url%(stronkaX),False,False)
            items.extend(nowy_link)
            self.progressDialogBG.update(0,message='Znalaz\xc5\x82em pozycji [%d] '%(len(items)))
        self.progressDialogBG.update(0,message='Indentyfikuje %d film\xc3\xb3w w %d w\xc4\x85tkach ...'%(len(items),self.fredy))
        items = [x for x in items if x.get('code','')!= '']
        printuj_linka('[AddMovie]: Found Total %d videos ... '%(len(items)))
        pool = thread_pool.ThreadPool(self.fredy)
        self.out=[]
        N=len(items)
        for idx,one in enumerate(items):
            pool.add_task(self.dod_Movies, *(one,idx,N))
            time.sleep(0.1)
        pool.wait_completion()
        printuj_linka('[AddMovie]: (After Threading) Found Total %d Movies ... '%(len(self.out)))
        self.out.reverse()
        self.progressDialogBG.close()
        self.add2( self.out )
        control.setSetting('library.service.last.run', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		
    def check_remove(self,folder_,idx,N):
        from shutil import rmtree
        sciezka2x = os.path.join(self.library_folder,folder_)
        content = control.listDir(sciezka2x)
        strmFile = [os.path.join(self.library_folder,folder_,x) for x in content[1] if x.endswith('.strm')]
        czas_progres = int((idx+1)*100.0/(N))
        self.progressDialogBG.update(czas_progres,message='%s'%(folder_))
        if strmFile:
            strmFile = strmFile[0]
            content = lib_tools.write_file2(strmFile)
            itemok = eval(urlparse.parse_qs(content.split('?')[-1]).get('ex_link',{})[0])
            hrefOut = itemok.get('url',[])
            check_time = itemok.get('linkchecked','2000-01-01 12:00:00')
            check_time = datetime.datetime.strptime(check_time, '%Y-%m-%d %H:%M:%S')
            obecnie_check = datetime.datetime.now() - check_time
            if obecnie_check.days >= self.t_link_delay:
                self.res['checked']+=1
                new_href=[new_hrefX for new_hrefX in set(hrefOut) if 'OK' in lib_tools.get_urlStat(new_hrefX)]
                printuj_linka('[CheckLink]: Checking %s links count before/after: %d/%d'%(folder_,len(hrefOut),len(new_href)))
                if len(new_href)==0:
                    rmtree(sciezka2x)
                    self.res['removed']+=1
                    printuj_linka('[CheckLink]: Removing Folder %s'%(folder_))
                else:
                    itemok.update( {'url':new_href, 'linkchecked': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') } )
                    content = lib_tools.build_url({'mode': 'lplay', 'ex_link':str(itemok)})
                    lib_tools.write_file(strmFile, content)
                    self.res['updated']+=1
                    printuj_linka('[CheckLink]: Updateing strmFile= %s'%(strmFile))
            else:
                self.res['skipped']+=1
                printuj_linka('[CheckLink]: Skipping %s already checked on %s'%(folder_,str(check_time)) )
				
    def CheckLinksInLibrary(self):
        import thread_pool
        import time
        self.t_link_delay =  int(control.setting('library.service.testlink.delay') or 0)
        if self.t_link_delay == 0:
            printuj_linka('[CheckLink]: START and STOP - Do not check library sources')
            return
        dirs,files = control.listDir(self.library_folder)
        self.progressDialogBG = control.progressDialogBG
        self.progressDialogBG.create('Sprawdzam \xc5\xbar\xc3\xb3d\xc5\x82a biblioteki cda.pl','Ilo\xc5\x9b\xc4\x87 pozycji: %d'%len(dirs))
        printuj_linka('[CheckLink]: START Library Folders = %d'%len(dirs))
        if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
            try:
                control.infoDialog('Sprawdzam \xc5\xbar\xc3\xb3dla biblioteki cda.pl', time=3)
                self.infoDialog = True
            except:
                self.infoDialog = False
        pool = thread_pool.ThreadPool(self.fredy)
        self.res={'checked':0,'skipped':0,'removed':0,'updated':0}
        N = len(dirs)
        for idx,folder_ in enumerate(dirs):
            pool.add_task(self.check_remove, *(folder_,idx,N))
            time.sleep(0.1)
        pool.wait_completion()
        printuj_linka('[CheckLink]: END Status checked:%d, skipped:%d, removed:%d, updated:%d'%(self.res['checked'],self.res['skipped'],self.res['removed'],self.res['updated']))
        self.progressDialogBG.close()
        if self.infoDialog == True:
            control.infoDialog('Usuni\xc4\x99to :%d, Zaktualizowano :%d '%(self.res['removed'],self.res['updated']), time=30)

