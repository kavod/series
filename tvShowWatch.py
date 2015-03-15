#!/usr/bin/env python
#encoding:utf-8

from __future__ import print_function
import sys
import os
from datetime import date
import string
import logging
import argparse
import unicodedata
from select import select
from subprocess import Popen, PIPE
from myDate import *
import Prompt
from TSWmachine import *
from myTvDB import *
from myConstants import *

load_directories()
API_FILE = myConstants.SCRIPT_PATH + '/TSW_api.py'

def input_serie():
	global t
	if 't' not in globals():
		t = myTvDB()
	else:
		logging.debug('connection saved')
	logging.debug('API initiator: %s', t)
	result = []
	while len(result) < 1:
		serie = Prompt.promptSimple("Please type your TV Show ")
		serie = str(''.join(c for c in unicodedata.normalize('NFKD', unicode(serie, 'utf-8')) if unicodedata.category(c) != 'Mn'))
		result = t.search(serie)

		if len(result) == 0:
			print("Unknowned TV Show")
		elif len(result) > 1:
			choices = []
			for val in result:
				if not 'firstaired' in val.keys():
					val['firstaired'] = '????'
				choices.append([val['id'],val['seriesname']+' (' + val['firstaired'][0:4] + ')'])
			result = Prompt.promptChoice("Did you mean...",choices)
			result = t[result]

		elif len(result) == 1:
			result = t[result[0]['id']]
	return result

def input_emails():
	emails = []
	email = 'start'
	while email != '':
		email = Prompt.promptSimple("Enter an email [keep blank to finish]")
		if email != '' and not re.match(r'[^@]+@[^@]+\.[^@]+',email):
			print('Incorrect format')
		elif re.match(r'[^@]+@[^@]+\.[^@]+',email):
			emails.append(email)
	return emails

def input_keywords():
	keywords = []
	keyword = 'start'
	while keyword != '':
		keyword = Prompt.promptSimple("Enter a keyword [keep blank to finish]")
		if keyword != '':
			keywords.append(keyword)
	return keywords

def select_episode(serie):
	s_choice = []
	seasons = (season for season in serie.getSeasons() if 
					season != "0" 
					and 'firstaired' in serie[int(season)][1].keys() 
					and serie[int(season)][1]['firstaired'] is not None
				)
	for season in seasons:
		try:
			s_choice.append([season,"Season " + season + " aired from " + serie[int(season)][1]['firstaired']])
		except:
			print(season)
			print(serie[int(season)][1].keys())
	season = int(Prompt.promptChoice("Please select season number",s_choice,len(s_choice)-1))
	
	s_choice = []
	episodes = (key for key,episode in serie[season].items())
	for episode in episodes:
		s_choice.append([str(episode),"\"" + serie[season][int(episode)]['episodename'] + "\" aired on " + serie[season][int(episode)]['firstaired']])
	episode = Prompt.promptChoice("Please select episode number",s_choice,len(s_choice)-1)
	return {
			'season':int(season),
			'episode':int(episode),
			'expected':serie[season][int(episode)]['firstaired']
			}

def last_or_next(serie):
	last = serie.lastAired()
	next = serie.nextAired()
	if (last is None):
		if Prompt.promptYN("Last season not yet started. Do you want to schedule the Season pilot on " + next['firstaired'],'y'):
			return next
		else:
			sys.exit()
	elif (next is None):
		if Prompt.promptYN("Last season achieved. Do you want to download the Season final on " + last['firstaired'],'n'):
			return last
		else:
			episode = select_episode(serie)
			return serie[episode['season']][episode['episode']]
			
	else:	
		print("Next episode download scheduled on " + next['firstaired'])
		str_last = 'Do you want also download the last aired : S{0:02}E{1:02} - {2} ?'
		if Prompt.promptYN(str_last.format(int(last['seasonnumber']),int(last['episodenumber']),last['firstaired']),'N'):
			return last
		else:
			return next

def keep_in_progress(tor):
	return tor.status == 'seeding'

def ignore_stopped(tor):
	return tor.status != 'stopped'

def action_run(m):
	result = m.getSeries()
	if result['rtn']=='300':
		print("No TV Show scheduled")
		sys.exit()
	if result['rtn']!='200':
		print('Error during TV Shows reading: '+result['error'])
		sys.exit()

	liste = result['result']
	cmdline = [
			sys.executable,	API_FILE,
			'-c',m.conffile.filename,
			'-s',m.seriefile.filename,
			'--action','run'
			]
	if m.getVerbosity():
		cmdline.append('-v')
	processes = [Popen(cmdline,stdout=PIPE,bufsize=1, close_fds=True, universal_newlines=True)]
	
	while processes:
	        for p in processes[:]:
	                if p.poll() is not None:
				result = p.stdout.read()
				fresult = result.split('|')
				if len(fresult)>2:
					print(str(next(x['name'] for x in liste if str(x['id'])==str(fresult[1])))+' : '+str(fresult[2]), end='')
	                        else:
					print(result, end='')
				p.stdout.close()
	                        processes.remove(p)
	        rlist = select([p.stdout for p in processes],[],[],0.1)[0]
	        for f in rlist:
			result = f.readline()
			fresult = result.split('|')
			if len(fresult)>2:
				print(str(next(x['name'] for x in liste if str(x['id'])==str(fresult[1])))+' : ' + str(fresult[2]), end='')
			else:
				print(result,end='')
        	        #print(f.readline(),end='')
	sys.exit()

def action_edit(m):
	global t
	logging.debug('Call function action_edit()')
	result = m.getSeries()
	logging.debug('result => '+str(result))
	if result['rtn']!='200' and result['rtn']!='300':
		print('Error during TV Shows reading: '+result['error'])
		sys.exit()
	if result['rtn'] == '300':
		print("No TV Show scheduled")
		sys.exit()
	pattern = '{0} - S{1:02}E{2:02} - expected on {3} (status: {4})'
	choice = []
	for serie in result['result']:
		choice.append([serie['id'],pattern.format(serie['name'],serie['season'],serie['episode'],serie['expected'],serie['status'])])
	serie_id = Prompt.promptChoice("Select TV Show to modify",choice,0)
	for serie in result['result']:
		if serie['id'] == serie_id:
			break
	logging.debug(serie)
	if (serie['keywords'] is not None):
	    keywords = ' / '.join(serie['keywords'])
	else:
	    keywords = ''
	if (serie['emails'] is not None):
	    emails = ' / '.join(serie['emails'])
	else:
	    emails = ''
	configData = Prompt.promptChoice(
            "Selection value you want modify for "+serie['name']+" ("+str(serie['id'])+"):",
            [
                ['pattern', 'Pattern:             '+serie['pattern']],
                ['episode', 'Episode:             '+'S{0:02}E{1:02}'.format(serie['season'],serie['episode'])],
                ['keywords','Search keywords:     '+keywords],
                ['emails',  'Notification emails: ' + emails]
            ])
	if configData == 'pattern':
		pattern = Prompt.promptSimple("Please enter the new search pattern:",serie['pattern'])
		serie['pattern'] = pattern
	if configData == 'episode':
		if 't' not in globals():
			t = myTvDB()
		else:
			logging.debug('connection saved')
		logging.debug('API initiator: %s', t)
		TVresult = t[serie['id']]
		episode = select_episode(TVresult)
		serie['season'] = episode['season']
		serie['episode'] = episode['episode']
		serie['expected'] = convert_date(episode['expected'])
	elif configData == 'emails':
		serie['emails'] = input_emails()
	elif configData == 'keywords':
		serie['keywords'] = input_keywords()
	else:
		sys.exit()
	rc = m.setSerie(serie['id'],{
					'pattern':serie['pattern'],
					'season':serie['season'],
					'episode':serie['episode'],
					'emails':serie['emails'],
					'keywords':serie['keywords'],
					'expected':serie['expected']
				},json_c=False)
	if rc['rtn'] == '200':
		print("TV Show updated")
	else:
		print("Error during TV Show update")

def action_list(m):
	logging.debug('Call function action_list()')
	result = m.getSeries('all',False)
	logging.debug('result => '+str(result))
	if result['rtn']!='200' and result['rtn']!='300':
		print('Error during TV Shows reading: '+result['error'])
		sys.exit()
	if result['rtn'] == '300':
		print("No TV Show scheduled")
		sys.exit()
	pattern = '{0}:{1} - S{2:02}E{3:02} - expected on {4} (status: {5})'
	for serie in result['result']:
		print(pattern.format(serie['id'],serie['name'],serie['season'],serie['episode'],serie['expected'],serie['status']))
	sys.exit()

def action_add(m):

	result = input_serie()
	if m.getSerie(result.data['id'])['rtn']=='200':
		print(messages.returnCode['409'])
		sys.exit()
	last = result.lastAired()
	next = result.nextAired()
	next = last_or_next(result)	
	#next = last_or_next(last,next)
	if m.testConf(False)['rtn']=='200' and Prompt.promptYN('Voulez-vous rajouter des emails de notification ?'):
		emails = input_emails()
	else:
		emails = []

	res = m.addSerie(result.data['id'],emails,next['seasonnumber'],next['episodenumber'])

	if res['rtn']!='200':
		print('Error during TV Show add: '+res['error'])
		sys.exit()
	print(result.data['seriesname'] + u" added")
	sys.exit()

def action_reset(m):
    '''Reset the configuration and/or the series list'''
    logging.debug('Call function action_reset()')
    result = {'rtn': '999'}
    while result['rtn'] != '200' and result['rtn'] != '302':
        conf = [
		'tracker_id', 
		'tracker_user',
		'tracker_password',
		'transmission_server',
		'transmission_port',
		'transmission_user',
		'transmission_password',
		'transmission_slotNumber',
		'transmission_folder'
		]
        for param in conf:
            result = m.setConf({param:'None'},False)
        if result['rtn'] == '200':
            result = m.testConf(False)
        if result['rtn'] != '200' and result['rtn'] != '302':
            print('Error during configuration: '+result['error'])

    if (Prompt.promptYN("Do you want to activate Email notification?",'N')):
        while result['rtn'] != '200':
            conf = [
		'smtp_server',
		'smtp_port',
		'smtp_ssltls',
		'smtp_user',
		'smtp_password',
		'smtp_emailSender',
		]
            for param in conf:
                result = m.setConf({param:'None'},False)
            if result['rtn'] == '200':
                result = m.testConf(True)
            if result['rtn'] != '200':
                print('Error during SMTP configuration: '+result['error'])

    result = m.setConf({},True)
    print('Configuration completed')

def action_del(m):
	'''Delete TV show from configuration file'''
	logging.debug('Call function action_del()')
	series = m.getSeries()
	if series['rtn'] == '300':
		print("No TV Show scheduled")
		sys.exit()
	if series['rtn'] != '200':
		print('Error during TV Show listing'+series['error'])
		sys.exit()
	choix = []
	if len(series['result'])>0:	
		for serie in series['result']:
			choix.append([serie['id'],serie['name']])
	else:
		print("No TV Show scheduled")
		sys.exit()
	s_id = Prompt.promptChoice("Which TV Show do you want to unschedule?",choix)
	result = m.delSerie(s_id)
	if result['rtn'] != '200':
		print('Error during Tv Show deletion'+result['error'])
	else:
		print('TV Show ' + str(s_id) + ' unscheduled')

def action_config(m):
    '''Change configuration'''
    logging.debug('Call function action_config()')
    conf = m.getConf()
    if (conf['rtn']!='200'):
        print("Error during configuration reading")
	sys.exit()
    conf = conf['result']
    if (conf['keywords'] is not None):
        keywords_default = ' / '.join(conf['keywords'])
    else:
        keywords_default = ''
    email_activated = 'Enabled' if len(conf['smtp'])>0 else 'Disabled'
    if ('folder' in conf['transmission'].keys()):
        folder = conf['transmission']['folder']
    else:
        folder = 'No transfer'
    if 'user' not in conf['tracker'] or conf['tracker']['user'] is None:
        conf['tracker']['user'] = ''

    configData = Prompt.promptChoice(
            "Selection value you want modify:",
            [
                ['tracker_id','Tracker : '+conf['tracker']['id']],
                ['tracker_user','Tracker Username : '+conf['tracker']['user']],
                ['tracker_password','Tracker Password : ******'],
                ['keywords','Torrent search keywords : '+keywords_default],
                ['transmission_server','Transmission Server : ' + str(conf['transmission']['server'])],
                ['transmission_port','Transmission Port : ' + str(conf['transmission']['port'])],
                ['transmission_user','Transmission User : ' + str(conf['transmission']['user'])],
                ['transmission_password','Transmission Password : ******'],
                ['transmission_slotNumber','Transmission maximum slots : ' + str(conf['transmission']['slotNumber'])],
                ['transmission_folder','Local folder : ' + str(conf['transmission']['folder'])],
                ['smtp','Email Notification: ' + email_activated]
            ])
    if configData == 'smtp':
        configData = Prompt.promptChoice(
            "Selection value you want modify:",
            [
                ['smtp_enable','Enable : ' + email_activated],
                ['smtp_server','SMTP Server : ' + str(conf['smtp']['server'])],
                ['smtp_port','SMTP Port : ' + str(conf['smtp']['port'])],
                ['smtp_ssltls','Secure connection : ' + str(conf['smtp']['ssltls'])],
                ['smtp_user','SMTP User : ' + str(conf['smtp']['user'])],
                ['smtp_password','SMTP Password : ******'],
                ['smtp_emailSender','Sender Email : ' + str(conf['smtp']['emailSender'])]
            ])
        if configData == 'smtp_enable':
            configData = Prompt.promptChoice(
				"Disable SMTP notification?",
				[
					[False,'Disable'],
					[True,'Enable']
				])
            m.conffile.confEmail(not configData)
            result = {'rtn':'200','result':'OK'}
        else:
            result = m.setConf({configData:'None'})
    else:
        result = m.setConf({configData:'None'})
    if result['rtn'] == '200':
        print('Configuration change completed !')
    else:
        print('Error during configuration change: '+result['error'])

def action_getconf(m):
    '''Return configuration'''
    logging.debug('Call function action_getconf()')
    conf = m.getConf()
    if (conf['rtn']!='200'):
        print("Error during configuration reading")
	sys.exit()
    conf = conf['result']
    result = "'tracker_id':"+conf['tracker']['id']
    result += "\n'tracker_user':"+conf['tracker']['user']
    result += "\n'transmission_server':" + str(conf['transmission']['server'])
    result += "\n'transmission_port':" + str(conf['transmission']['port'])
    result += "\n'transmission_user':" + str(conf['transmission']['user'])
    result += "\n'transmission_slotNumber':" + str(conf['transmission']['slotNumber'])
    if 'folder' in conf['transmission'].keys():
        result += "\n'transmission_folder':" + str(conf['transmission']['folder'])
    if len(conf['smtp'])>0:
        result += "\n'smtp_server':" + str(conf['smtp']['server'])
        result += "\n'smtp_port':" + str(conf['smtp']['port'])
        result += "\n'smtp_ssltls':" + str(conf['smtp']['ssltls'])
        result += "\n'smtp_user':" + str(conf['smtp']['user'])
        result += "\n'smtp_emailSender':" + str(conf['smtp']['emailSender'])
    for keyword in conf['keywords']:
        result += "\n'keywords':" + keyword
    print(result)

def main():
    # Get input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-a",
            "--action",
            default='run',
            choices=['run', 'list', 'init', 'add','config','getconf','del','edit'],
            help='action triggered by the script'
        )
    parser.add_argument(
            "-c",
            "--config",
            default=myConstants.CONFIG_FILE,
            help='indicates the configuration file location. By default:'+myConstants.CONFIG_FILE
        )
    parser.add_argument(
            "-s",
            "--seriefile",
            default=myConstants.LIST_FILE,
            help='indicates the series list file location. By default:'+myConstants.LIST_FILE
        )
    parser.add_argument(
            "-v",
            "--verbosity",
            action="store_true",
            help='maximum output verbosity'
        )
    parser.add_argument(
            "--arg",
            default='',
            help='arguments for bash execution'
        )
    args = parser.parse_args()

    # Manage verbosity level
    if args.verbosity:
        logging.basicConfig(level=logging.DEBUG)
        verbose = True
    else:
        verbose = False
    logging.info('SERIES started in verbosity mode')

    global arg;
    if args.arg != '':
        Prompt.arg = args.arg.split(',')

    # Initialize more data
    m = TSWmachine(True,verbose)
    if args.action != 'init':
		logging.debug('Loading of conffile: %s', args.config)
		logging.debug('Loading of seriefile: %s', args.seriefile)
		result = m.openFiles(args.config, args.seriefile)
		if result['rtn']!='200':
			print("Please first use tvShowWatch --action init")
			sys.exit()
    else:
        result = m.createConf(args.config)
        if result['rtn']!='200':
            print('Error during creation of the configuration file: '+result['error'])
            sys.exit()

    action_fct = {
            'list':action_list,
            'run':action_run,
            'add':action_add,
            'init':action_reset,
            'config':action_config,
            'del':action_del,
            'edit':action_edit,
            'getconf':action_getconf
        }

    # Call for action
    logging.debug('Action from the parameter: %s', args.action)
    
    fct = action_fct[args.action]
    logging.debug('Action function: %s', fct)
    fct(m)

if __name__ == '__main__':
    main()

