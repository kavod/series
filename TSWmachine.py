#!/usr/bin/env python
#encoding:utf-8

import os
import sys
import messages
import logging
from datetime import date
import transmissionrpc
from tracker import *
from myDate import *
from ConfFile import ConfFile
from serieList import SerieList
from functions import *
from myTvDB import *
from logger import *

CONFIG_FILE = sys.path[0] + '/config.xml' if sys.path[0] != '' else 'config.xml'
LIST_FILE = sys.path[0] + '/series.xml' if sys.path[0] != '' else 'series.xml'

global t

class TSWmachine:
	def __init__(self,admin=False,log=False):
		if log:
			logging.basicConfig(level=logging.DEBUG)
		self.admin = admin
		self.conffile = ConfFile()
		self.seriefile = SerieList()
		self.verbosity = log
	
	def getVerbosity(self):
		return self.verbosity

	def getAuth(self):
		logging.info('Get Auth :'+ str(self.admin))
		return self.admin

	def openFiles(self,conffile=CONFIG_FILE,seriefile=LIST_FILE):
		logging.info('OpenFile ' + str(conffile) + ' and '+ str(seriefile))
		result = self.conffile.openFile(str(conffile))
		if (result['rtn']!='200'):
			logging.info('Fail to open file:'+ str(conffile))
			return result
		logging.info('Conf file OK, opening Serie List')
		return self.seriefile.openFile(seriefile)

	def openedFiles(self,files=['conf','serie']):
		logging.info('OpenedFile')
		if 'conf' in files and self.conffile.openedFile()['rtn']!='200':
			logging.info('Conf file not opened')
			return self.conffile.openedFile()
		if 'serie' in files and self.seriefile.openedFile()['rtn']!='200':
			logging.info('Serie file not opened')
			return self.seriefile.openedFile()
		return {'rtn':'200','error':messages.returnCode['200']}

	def createConf(self,filename,conf={}):
		logging.info('CreateConf ' + str(filename) + ' with '+ str(conf))
		if (not self.getAuth()):
			return {'rtn':'406','error':messages.returnCode['406']}
		self.conffile.createBlankFile(filename)
		if len(conf.keys())>0:
			return self.setConf(conf)
		else:
			return {'rtn':'200','error':messages.returnCode['200']}

	def getConf(self,conf='all'):
		if (not self.openedFiles(['conf'])['rtn']=='200'):
			return self.openedFiles(['conf'])
		tracker = self.conffile.getTracker()
		tracker['password'] = '****'
		transmission = self.conffile.getTransmission()
		transmission['password'] = '****'
		email = self.conffile.getEmail()
		email['password'] = '****'
		keywords = self.conffile.getKeywords()
		result = {}
		if conf=='all':
			result = {'tracker':tracker,'transmission':transmission,'smtp':email,'keywords':keywords}
		else:
			for parameter in conf:
				if parameter.split('_')[0] == 'tracker':
					if ('tracker' not in result.keys()):
						result['tracker']={}
					result['tracker'][parameter.split('_')[1]] = tracker[parameter.split('_')[1]]
				if parameter.split('_')[0] == 'transmission':
					if ('transmission' not in result.keys()):
						result['transmission']={}
					result['transmission'][parameter.split('_')[1]] = transmission[parameter.split('_')[1]]
				if parameter.split('_')[0] == 'smtp':
					if ('smtp' not in result.keys()):
						result['email']={}
					if parameter.split('_')[1] in email.keys():
						result['smtp'][parameter.split('_')[1]] = email[parameter.split('_')[1]]
					else:
						result['smtp'][parameter.split('_')[1]] = ''
				if parameter == 'keywords':
					result['keywords'] = keywords
					
		return {'rtn':'200','result':result}

	def setConf(self,conf={},save=True):
		if (not self.getAuth()):
			return {'rtn':'406','error':messages.returnCode['406']}
		if (not self.openedFiles(['conf'])['rtn']=='200'):
			return {'rtn':'403','error':messages.returnCode['403'].format('Configuration')}

		send = False
		conf = convert_conf(conf)
		original_len = 0
		final_len = 0
		for key, value in conf.iteritems():
			if key.split('_')[0] in ['tracker','transmission','smtp']:
				if key == 'smtp_enable' and value == 'False':
					self.conffile.confEmail(True)
				if (self.conffile.change(key,value)==False):
					return {'rtn':'400','error':messages.returnCode['400'].format(key)}
				if key.split('_')[0] == 'smtp':
					send = True
			elif key == 'keywords':
				original_len = len(value)
				value = [x for x in value if x != '']
				final_len = len(value)
				if final_len < 1:
					value = 'None';
				if (self.conffile.changeKeywords(value)==False):
					return {'rtn':'400','error':messages.returnCode['400'].format(key)}
			else:
				return {'rtn':'400','error':messages.returnCode['400'].format(key)}
		if save:
			self.conffile._save()
			result = self.testConf(send)
			if result['rtn'] == '200':
				if original_len == final_len:
					return result
				else:
					return {'rtn':'304','error':messages.returnCode['304'].format(key)}
			return result
		else:	
			return {'rtn':'200','error':messages.returnCode['200']}

	def testConf(self,send=False):
		logging.info('testConf ')
		opened = self.openedFiles(['conf'])
		if (opened['rtn'] != '200'):
			return opened

		tracker = self.conffile.testTracker()
		if (tracker['rtn'] != '200'):
			return tracker

		transmission = self.conffile.testTransmission()
		if (transmission['rtn'] != '200'):
			return transmission

		email = self.conffile.testEmail(send)
		if (email['rtn'] != '200' and email['rtn'] != '405'):
			return email

		if email['rtn'] == '405':
			return {'rtn':'302','error':messages.returnCode['302']}
		else:
			return {'rtn':'200','error':messages.returnCode['200']}

	def getSerie(self,s_id,json_c=False,load_tvdb=False):
		logging.info('getSerie ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		liste = self.seriefile.listSeries(json_c,load_tvdb)
		if liste == False:
			return {'rtn': 404,'error':messages.returnCode['404'].format('TvDB','') }
		if len(liste)>0:
			if isinstance(s_id,int) or (isinstance(s_id,basestring) and s_id.isdigit()):
				result = [x for x in liste if x['id'] == int(s_id)]
				if len(result)>0:
					return {'rtn':'200','result':result[0]}
				else:
					return {'rtn':'408','error':messages.returnCode['408'].format(str(s_id))}
			elif isinstance(s_id,basestring):
				result = [x for x in liste if x['name'] == s_id]
				if len(result)>0:
					return {'rtn':'200','result':result[0]}
				else:
					return {'rtn':'408','error':messages.returnCode['408'].format(str(s_id))}
			else:
				return {'rtn':'407','error':messages.returnCode['407'].format(str(s_id))}
		else:
			return {'rtn':'300','error':messages.returnCode['300']}

	def getSeries(self,s_ids='all',json_c=False,load_tvdb=False):
		logging.info('getSeries ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if s_ids == 'all':
			serielist = self.seriefile.listSeries(json_c,load_tvdb)
			if serielist == False:
				return {'rtn': 404,'error':messages.returnCode['404'].format('TvDB','') }
			if len(serielist)>0:
				return {'rtn':'200','result':[x for x in serielist]}
			else:
				return {'rtn':'300','error':messages.returnCode['300']}
		elif isinstance(s_ids,int) or (isinstance(s_ids,basestring) and s_ids.isdigit()):
			return self.getSerie(s_ids)
		elif isinstance(s_ids,list):
			result = []
			for s_id in s_ids:
				res_serie = self.getSerie(s_id,json_c)
				if res_serie['rtn']!='200':
					result.append(res_serie['result'])
				else:
					return res_serie
			return {'rtn':'200','result':result}
		else:
			return {'rtn':'407','error':messages.returnCode['407'].format(str(s_ids))}

	def addSerie(self,s_id,emails=[],season=0,episode=0):
		logging.info('addSerie ' + str(s_id) + '/'+str(emails)+'/'+str(season)+'/'+str(episode))
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if self.getSerie(s_id)['rtn']=='200':
			return {'rtn':'409','error':messages.returnCode['409']}

		serie = last_aired(int(s_id),int(season),int(episode))
		if len(serie.keys())<1:
			return {'rtn':'408','error':messages.returnCode['408'].format(str(s_id))}
		episode = serie['next']
		if episode is None:
			# If TV show is achieved, just add it without episode scheduled
			#return {'rtn':'410','error':messages.returnCode['410']}
			episode = None
		else:
			episode = {'season':episode['seasonnumber'],'episode':episode['episodenumber'],'aired':convert_date(episode['firstaired'])}
		if self.seriefile.addSerie(serie['id'],serie['seriesname'],episode,emails,self.conffile.getKeywords()):
			return {'rtn':'200','error':messages.returnCode['200']}
		else:
			return {'rtn':'411','error':messages.returnCode['411'].format(s_id)}

	def addSeries(self,s_ids,emails=[]):
		logging.info('addSeries')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if isinstance(s_ids,int):
			return self.addSerie(s_ids,emails)
		elif isinstance(s_ids,list):
			result = []
			for s_id in s_ids:
				res_serie = self.addSerie(s_id,emails)
				res_serie.update({'id':s_id})
				result.append(res_serie)
				if res_serie['rtn'] != '200':
					return {'rtn':'412','error':messages.returnCode['412'],'result':result}
			return {'rtn':'200','result':result}
		else:
			return {'rtn':'411','error':messages.returnCode['411'].format(s_id)}

	def _setSerie(self,s_id,result,emails,keywords,param={}):
		error = False
		if len(result)>0:
			if (self.seriefile.updateSerie(result['id'],param)):
				if emails is not None:
					if(not self.seriefile.changeEmails(result['id'],emails)):
						error = True
				if keywords is not None:
					if(not self.seriefile.changeKeywords(result['id'],keywords)):
						error = True
				if error:
					return {'rtn':'417','error':messages.returnCode['417'].format(result['name'])} #Error during update
				else:
					return {'rtn':'200','error':messages.returnCode['200']}
			else:
				return {'rtn':'417','error':messages.returnCode['417'].format(result['name'])} #Error during update
		else:
			return {'rtn':'408','error':messages.returnCode['408'].format(str(s_id))} #Not found

	def setSerie(self,s_id,param={},json_c=False):
		logging.info('getSerie ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if not all(y in ['emails','season','episode','expected','status','keywords','pattern'] for y in param.keys()):
			return {'rtn':'400','error':messages.returnCode['400'].format(str(param.keys()))}
		if 'emails' in param.keys():
			emails = param.pop('emails')
		else:
			emails = None
		if 'keywords' in param.keys():
			keywords = param.pop('keywords')
		else:
			keywords = None
		liste = self.seriefile.listSeries(json_c)
		if liste == False:
			return {'rtn': 404,'error':messages.returnCode['404'].format('TvDB','') }
		if len(liste)>0:
			if isinstance(s_id,int) or (isinstance(s_id,basestring) and s_id.isdigit()):
				result = [x for x in liste if x['id'] == int(s_id)]
				return self._setSerie(s_id,result[0],emails,keywords,param)
			elif isinstance(s_id,basestring):
				result = [x for x in liste if x['name'] == s_id]
				return self._setSerie(s_id,result[0],emails,keywords,param)
			else:
				return {'rtn':'407','error':messages.returnCode['407'].format(str(s_id))}
		else:
			return {'rtn':'300','error':messages.returnCode['300']}

	def resetKeywords(self,s_id):
		logging.info('resetKeywords ' + str(s_id))
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		keywords = self.conffile.getKeywords()
		return self.setSerie(s_id,{'keywords':keywords},False)

	def resetAllKeywords(self):
		logging.info('resetAllKeywords ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		keywords = self.conffile.getKeywords()
		series = self.getSeries('all',False,False)
		if len(series)<1:
			return {'rtn':'300','error':messages.returnCode['300']}
		for serie in series['result']:
			result = self.resetKeywords(serie['id'])
			if result['rtn'] != '200':
				break
		return result

	def delSerie(self,s_id):
		logging.info('delSerie ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		serie = self.getSerie(s_id)
		if serie['rtn'] != '200':
			return serie
		result = self.seriefile.delSerie(s_id)
		if result:
			return {'rtn':'200','error':messages.returnCode['200']}
		else:
			return {'rtn':'413','error':messages.returnCode['413'].format(s_id)}
	
	def delSeries(self,s_ids=''):
		logging.info('delSeries ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if s_ids == '':
			return {'rtn':'416','error':messages.returnCode['416']}
		if s_ids == 'all':
			series = self.getSeries()
			if series['rtn'] != '200':
				return series
			else:
				s_ids = [x['id'] for x in series['result']]
		if isinstance(s_ids,int):
			return self.delSerie(s_ids)
		elif isinstance(s_ids,list):
			result = []
			for s_id in s_ids:
				res_serie = self.delSerie(s_id)
				res_serie.update({'id':s_id})
				result.append(res_serie)
				if res_serie['rtn'] != '200':
					return {'rtn':'414','error':messages.returnCode['412'],'result':result}
			return {'rtn':'200','result':result}
		else:
			return {'rtn':'411','error':messages.returnCode['411'].format(s_id)}

	def pushTorrent(self,serieID,filepath):
		logging.info('pushTorrent ')
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			return opened
		if int(serieID) == 0:
			return {'rtn':'416','error':messages.returnCode['416']}
		result = self.getSerie(serieID,json_c=False,load_tvdb=True)
		if (result['rtn'] != '200'):
			return result
		serie = result['result']
		if (not os.path.isfile(filepath)):
			return {'rtn':'422','error':messages.returnCode['422'].format(filepath)}
		if (serie['status'] in [10,15,20]): # Status waiting for broadcast / waiting for run / searching torrent
			season = int(serie['season'])
			episode = int(serie['episode'])
			result = self.getEpisode(serieID,season,episode)
			if (season * episode > 0 and result['rtn']=='200'):
				confTransmission = self.conffile.getTransmission()
				tc = transmissionrpc.Client(
						confTransmission['server'],
						confTransmission['port'],
						confTransmission['user'],
						confTransmission['password']
					)
				new_torrent = add_torrent('file://' +filepath, tc, confTransmission['slotNumber'],confTransmission['folder'] is not None)
				self.seriefile.updateSerie(serie['id'],{'status':30, 'slot_id':new_torrent.id})
				return {'rtn':'230','error':messages.returnCode['230']}
		return {'rtn':'421','error':messages.returnCode['421']}
		
		
	def run(self):
		logging.info('Run !!! ')
		logger = Logger()
		opened = self.openedFiles()
		if opened['rtn'] != '200':
			print("{0}|{1}".format(opened['rtn'],opened['error']))
			return
		testconf = self.testConf()
		if testconf['rtn'] != '200' and testconf['rtn'] != '302':
			print("{0}|{1}".format(testconf['rtn'],testconf['error']))
			return
		conf = self.conffile.getTracker()
		try:
			tracker = Tracker(conf['id'],{'username':conf['user'],'password':conf['password']})
		except InputError as e:
			print(e.msg)
			return
		series = self.seriefile

		str_search = '{0} S{1:02}E{2:02} {3}'
		str_result = "{0}|{1}|{2}"
		
		liste = series.listSeries()
		if liste == False:
			return {'rtn': 404,'error':messages.returnCode['404'].format('TvDB','') }

		if (len(liste)<1):
			print("{0}|{1}".format('300',messages.returnCode['300']))
			return

		for serie in liste:
			if serie['status'] == 90 or serie['episode'] == 0: # If last episode reached
				print(str_result.format('303',str(serie['id']),messages.returnCode['303']))
				continue

			
			str_search_list = []
			for keyword in serie['keywords']:
				str_search_list.append(str_search.format(
						serie['pattern'],
						int(serie['season']),
						int(serie['episode']),
						keyword
							))
			if (len(str_search_list)<1):
				str_search_list.append(str_search.format(
                                                serie['name'],
                                                int(serie['season']),
                                                int(serie['episode']),
                                                ''
                                                        ))
			confTransmission = self.conffile.getTransmission()
			if int(serie['status']) == 30: # Torrent already active
				if 'tc' not in locals():
					tc = transmissionrpc.Client(
						confTransmission['server'],
						confTransmission['port'],
						confTransmission['user'],
						confTransmission['password']
					)
				else:
					logging.info('connection saved')

				tor_found = False
				for tor in tc.get_torrents(): # Check if torrent still there!
					if tor.id == serie['slot_id']:
						tor_found = True
						break
				if not tor_found:
					self.seriefile.updateSerie(serie['id'],{'status':10,'slot_id':0})
				else:
					torrent = tc.get_torrent(serie['slot_id'])
					if torrent.status == 'seeding':
						if(confTransmission['folder'] is not None):
							if (transferFile(torrent.files(),serie,confTransmission)):
								content = str_search_list[0] + ' broadcasted on ' + print_date(serie['expected']) + ' download completed'
								sendEmail(content,serie,self.conffile)
							else:
								print(str_result.format('418',str(serie['id']),messages.returnCode['418']))
								continue
						next = next_aired(serie['id'],serie['season'],serie['episode'])
						self.seriefile.updateSerie(serie['id'],next)
						if next['status'] == 90:
							logger.append(serie['id'],'260',{"season":serie['season'],"episode":serie['episode']})
							print(str_result.format('260',str(serie['id']),messages.returnCode['260']))
						else:
							logger.append(serie['id'],'260',{"season":serie['season'],"episode":serie['episode']})
							print(str_result.format('250',str(serie['id']),messages.returnCode['250']))
					else:
						print(str_result.format('240',str(serie['id']),messages.returnCode['240']))
					continue

			if int(serie['status']) in [10,15,20,21] and serie['expected'] < date.today(): # If episode broadcast is in the past
				if conf['id'] == 'none':
					self.seriefile.updateSerie(serie['id'],{'status':21})
					logger.append(serie['id'],'221',{"season":serie['season'],"episode":serie['episode']})
					print(str_result.format('221',str(serie['id']),messages.returnCode['221']))
				else:
					if 'tc' not in locals():
						tc = transmissionrpc.Client(
							confTransmission['server'],
							confTransmission['port'],
							confTransmission['user'],
							confTransmission['password']
						)
					else:
						logging.info('connection saved')

					self.seriefile.updateSerie(serie['id'],{'status':20})
					for search in str_search_list:
						try:
							result = tracker.search(search)
						except requests.exceptions.ConnectionError as e:
							print(e)
							sys.exit()
						nb_result = len(result)
						logging.debug(search + ":" + str(nb_result) + ' result(s)')

						if nb_result > 0: # If at least 1 relevant torrent is found
							result = tracker.select_torrent(result)
							logging.debug("selected torrent:")
							logging.debug(result)
							torrent = tracker.download(result['id'])
							new_torrent = add_torrent(torrent, tc, confTransmission['slotNumber'],confTransmission['folder'] is not None)
							self.seriefile.updateSerie(serie['id'],{'status':30, 'slot_id':new_torrent.id})
							break
					if nb_result > 0:
						print(str_result.format('230',str(serie['id']),messages.returnCode['230']))
					else:
						print(str_result.format('220',str(serie['id']),messages.returnCode['220']))
			else:
				self.seriefile.updateSerie(serie['id'],{'status':10})
				print(str_result.format('210',str(serie['id']),messages.returnCode['210']))

	def getEpisode(self,serieID,season,episode):
		t = myTvDB()
		try:
			result = t[serieID][season][episode]
			return {'rtn':'200','result':result}
		except Exception,e:
			return {'rtn':'419','error':messages.returnCode['419']}

	def search(self,pattern):
		t = myTvDB()
		try:
			result = t.search(pattern)
			if len(result)>0:
				return {'rtn':'200','result':result}
			else:
				return {'rtn':'408','error':messages.returnCode['408'].format(pattern)}
		except Exception,e:
			return {'rtn':'419','error':messages.returnCode['404'].format('TvDB')}

	def logs(self,json_c=False):
		t = myTvDB()
		logger = Logger()
		if json_c:
			result = [ convert_dt2str(i) for i in logger.filter_log()]
		else:
			result = logger.filter_log()
		for i in result:
			i['msg'] = messages.returnCode[i['rtn']]
			if 'args' in i.keys():
				i['msg'] = i['msg'].format(i['args'])
			i['seriesname'] = t[i['serieID']]['seriesname']


		return {'rtn':'200','result': result}

