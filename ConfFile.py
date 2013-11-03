#!/usr/bin/env python
#encoding:utf-8

import os
import sys
import xml.etree.ElementTree as ET
import transmissionrpc
from Prompt import *
from myDate import *
from tracker import *

CONFIG_FILE = 'series.xml'
CONFIG_VERSION = '1.5'

TORRENT_STATUS = {
			10: 'Waiting Broadcast',
			20: 'Waiting Torrent',
			30: 'Leeching'
		}

class ConfFile:
	"""
		The ``ConfFile`` constructor
		============================
		
		Create the ConfFile object
		
		:param filename: Filename
		:type question: string


		:Example:

		>>> f = ConfFile()		
	"""
	def __init__(self, filename = CONFIG_FILE):
		self.filename = filename
		if not self.testFileExists():
			print("Initial configuration")
			self._create()
		else:
			self.tree = ET.parse(self.filename)
			if self.getVersion() != CONFIG_VERSION:
				if promptYN("Your configuration file version ({0}) is obsolet (<{1}). Do you want reset it?".format(self.getVersion(),CONFIG_VERSION),'N'):
					self._create()
				else:
					sys.exit()

	"""
		The ``_create`` method
		=============================
		
		Use it for create a blank configuration file.

		.. warnings:: No confirmation required. If file already exists, it will be erase!!!
		.. seealso:: ``reset``

		:return: True if file creation is OK
		:rtype: boolean

		:Example:

		>>> f._create()
		True
		
	"""
	def _create(self):
		tracker_conf = self.confTracker()
		tc_conf = self.confTransmission()

		conf = ET.Element("conf")
		self.tree = ET.ElementTree(conf)
		version = ET.SubElement(conf,'version')
		version.text = CONFIG_VERSION

		# Tracker conf
		tracker = ET.SubElement(conf, "tracker")
		tracker.text = str(tracker_conf[0])
		s_username = ET.SubElement(conf, "user")
		s_username.text = str(tracker_conf[1])
		s_password = ET.SubElement(conf, "password")
		s_password.text = str(tracker_conf[2])
		s_keywords = ET.SubElement(conf, "keywords")
		s_keywords.text = ''

		# Transmission conf
		transmission = ET.SubElement(conf, "transmission")
		tc_server = ET.SubElement(transmission, "server")
		tc_server.text = str(tc_conf['server'])
		tc_port = ET.SubElement(transmission, "port")
		tc_port.text = str(tc_conf['port'])
		tc_user = ET.SubElement(transmission, "user")
		tc_user.text = str(tc_conf['user'])
		tc_password = ET.SubElement(transmission, "password")
		tc_password.text = str(tc_conf['password'])
		tc_slotNumber = ET.SubElement(transmission, "slotNumber")
		tc_slotNumber.text = str(tc_conf['slotNumber'])
		

		self._save()
		return True

	"""
		The ``_save`` method
		====================
		
		Save configuration in config file

		:return: True if file saving is OK
		:rtype: boolean

		:Example:

		>>> f._save()
		True
		
	"""
	def _save(self):
		self.tree.write(self.filename)	

	"""
		The ``testFileExists`` method
		=============================
		
		Use it in order to test if configuration file exists

		:return: True if file exists
		:rtype: boolean

		:Example:

		>>> f._testFileExists()
		True
		
	"""
	def testFileExists(self):
		if os.path.isfile(self.filename): 
			conffile = open(self.filename, 'r')
			conffile.readlines()
			conffile.close()
			return True

	"""
		The ``addSerie`` method
		=============================
		
		Use it in order to add an additional TV show in configuration file

		:param s_id: TvDB ID of the TV show
		:type question: Integer

		:param s_season: TV Show season number
		:type question: Integer

		:param s_episode: TV Show episode number of the season
		:type question: Integer

		:return: True when append of the TV Show completed
		:rtype: boolean

		:Example:

		>>> f._testFileExists()
		True
		
	"""
	def addSerie(self, s_id, s_season, s_episode):
		if not self.testFileExists():
			self._create()

		if self.testSerieExists(s_id):
			print('TV Show already scheduled')
			return False
 
		conf = self.tree.getroot()		
		serie = ET.SubElement(conf, "serie")
		serie_id = ET.SubElement(serie, "id")
		serie_id.text = str(s_id)
		serie_s = ET.SubElement(serie, "season")
		serie_s.text = str(s_season)
		serie_e = ET.SubElement(serie, "episode")
		serie_e.text = str(s_episode)
		status = ET.SubElement(serie, "status")
		status.text = str(10)
		slot_id = ET.SubElement(serie, "slot_id")
		slot_id.text = str(0)
		#ET.dump(conf)
		self._save()
		return True

	def delSerie(self, s_id):
		result = False
		conf = self.tree.getroot()
		for serie in conf.findall('serie'):
			if serie.find('id').text == str(s_id):
				conf.remove(serie)
				result = True
		self._save()
		return result

	"""
		The ``testSerieExists`` method
		==============================
		
		Use it in order to know if a TV show already is in configuration file

		:param s_id: TvDB ID of the TV show
		:type question: Integer

		:return: True if TV Show is in the configuration file
		:rtype: boolean

		:Example:

		>>> f.testSerieExists(5262)
		False
		
	"""
	def testSerieExists(self, s_id):
		if not self.testFileExists():
			self._create()
			return False
		
		self.tree = ET.parse(self.filename)
		conf = self.tree.getroot()

		for serie in conf.findall('serie'):
			if serie.find('id').text == str(s_id):
				return True
		return False

	"""
		The ``reset`` method
		====================
		
		Use it in order to reset configuration file.

		:return: True if reset completed
		:rtype: boolean

		:Example:
		>>> f.reset()
		Are you sure you want to delete configuration? [y/N]
		n
		False
		
	"""
	def reset(self):
		if promptYN("Are you sure you want to delete configuration?",'N'):
			self._create()
			print("Configuration file reseted")
			return True
		return False

	"""
		The ``listSeries`` method
		=========================
		
		Return the list of TV Shows in configuration file

		:return: list of TV Shows ID
		:rtype: list of Integers

		:Example:
		f.listSeries()
		[542,5428,45758]
		
	"""
	def listSeries(self):
		result = []
		conf = self.tree.getroot()
		for serie in conf.findall('serie'):
			result.append({
				'id': int(serie.find('id').text),
				'season': int(serie.find('season').text),
				'episode': int(serie.find('episode').text),
				'status': int(serie.find('status').text),
				'slot_id': int(serie.find('slot_id').text)
					})
		return result

	def getVersion(self):
		conf = self.tree.getroot()
		return conf.find('version').text

	"""
		The ``confTracker`` method
		=========================
		
		Create Tracker configuration

		:return: list [tracker ID, username, password]
		:rtype: list of strings

		:Example:
		f.confTracker()
		['t411', 'obiWan', '1324']
		
	"""
	def confTracker(self):
		while True:	
			tracker_id = self.select_tracker()
			username = self.select_user()
			password = self.select_password()
			
			tracker = Tracker(tracker_id,username,password)
			if tracker.test():
				break
			print('Invalid authentification')

		return [tracker_id, username, password]

	"""
		The ``confTransmission`` method
		===============================
		
		Create Transmission configuration

		:return: {'server', 'port', 'username', 'password', 'slotNumber'}
		:rtype: dict

		:Example:
		f.confTransmission()
		{
			'server':	'localhost',
			'port':		'9091',
			'username':	'ObiWan',
			'password':	'1234',
			'slotNumber':	6
		}
		
	"""
	def confTransmission(self):
		while True:	
			server = self.select_transmissionServer()
			port = int(self.select_transmissionPort())
			user = self.select_transmissionUser()
			password = self.select_transmissionPassword()
			slot_number = self.select_transmissionSlotNumber()
			
			try:
				self.tc = transmissionrpc.Client(server, port, user, password)
			except Exception as inst:
				print('Transmission authentification failed')
			else:
				break

		return {
			'server':	server,
			'port':		port,
			'user':		user,
			'password':	password,
			'slotNumber':	slot_number
			}

	def getTracker(self):
		conf = self.tree.getroot()
		keywords = conf.find('keywords').text if conf.find('keywords').text is not None else '' 
		return [conf.find('tracker').text,conf.find('user').text,conf.find('password').text,keywords]

	def getTransmission(self):
		transmission = self.tree.getroot().find('transmission')
		return {
			'server':	transmission.find('server').text,
			'port':		transmission.find('port').text,
			'user':		transmission.find('user').text,
			'password':	transmission.find('password').text,
			'slotNumber':	transmission.find('slotNumber').text
			}

	def select_tracker(self):
		return promptChoice("Please select your tracker:",TRACKER_CONF)

	def select_transmissionServer(self):
		return promptSimple('Enter your Transmission server:','localhost')

	def select_transmissionPort(self):
		return int(promptSimple('Enter your Transmission port:','9091'))

	def select_transmissionUser(self):
		return promptSimple('Enter your Transmission username:')

	def select_transmissionPassword(self):
		return promptPass('Enter your Transmission password:')

	def select_transmissionSlotNumber(self):
		return promptSimple('Enter your maximum slot number:','6')

	def select_user(self):
		return promptSimple('Enter your username:')

	def select_password(self):
		return promptPass('Enter your password:')

	def select_keywords(self):
		return promptSimple('Enter your default keywords:')

	def change(self,configData):
		value = getattr(self, "select_" + configData)()
		conf = self.tree.getroot()
		conf.find(configData).text = str(value)
		self._save()
		
	def updateSerie(self,s_id,values):
		result = False
		conf = self.tree.getroot()
		for serie in conf.findall('serie'):
			if serie.find('id').text == str(s_id):
				for val in values.keys():
					serie.find(val).text = str(values[val])
				result = True
		self._save()
		return result

		
