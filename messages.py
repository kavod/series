global returnCode

returnCode = {
	'100': 'TV Show modified',
	'101': 'TV Show scheduled',
	'102': 'TV Show keywords reseted',
	'103': 'TV Show unscheduled',
	'104': 'Torrent manually pushed',
	'105': 'Torrent not found in Transmission. Reseting status',

	'200': 'OK',
	'210': 'Not yet aired',
	'220': 'Torrent not found',
	'221': 'No tracker configured',
	'230': 'Torrent added',
	'240': 'Torrent in progress',
	'250': 'Torrent downloaded and next episode scheduled',
	'260': 'Torrent download and final episode',

	'300': 'No TV Show scheduled',
	'301': 'Broadcast achieved - No more episode - Removing from list',
	'302': 'Configuration OK without SMTP',
	'303': 'Broadcast achieved - No more episode',
	'304': 'Keywords updated but blank values ignored',

	'400': 'Unknown parameter {0}',
	'401': '{0} not found',
	'402': '{0} file version ({1}) is obsolet (<{2}).',
	'403': 'No opened file for {0}',
	'404': 'Connection error on {0}: {1}',
	'405': 'No configuration for {0}',
	'406': 'Admin authentification required',
	'407': 'Incorrect parameter: {0}',
	'408': 'TV Show not found: {0}',
	'409': 'Already scheduled TV Show',
	'410': 'Next episode not scheduled',
	'411': 'Error during adding {0}',
	'412': 'Incomplete TV Show adding',
	'413': 'Error during deletion of {0}',
	'414': 'Incomplete TV Show deletion',
	'415': 'Unable to parse arguments',
	'416': 'You must provide ID of TV Show you want to delete or \'all\' for global reset',
	'417': 'Error during updating {0}',
	'418': 'Error during transfer',
	'419': 'Unknow episode reference',
	'420': 'Blank keyword is ignored',
	'421': 'Torrent cannot be pushed',
	'422': 'File {0} does not exists',
	'422': 'Tracker {0} requires username/password',
	'499': 'General Error'
	}