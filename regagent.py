from twisted.internet import reactor
from twisted.internet.task import LoopingCall

# Logging
from twisted.python import syslog
from twisted.python.log import msg
from twisted.python.log import err

from sippy.SipTransactionManager import SipTransactionManager
from sippy.UA import UA
from sippy.SipAuthorization import SipAuthorization
from sippy.SipCallId import SipCallId
from sippy.SipFrom import SipFrom
from sippy.SipTo import SipTo
from sippy.SipURL import SipURL
from sippy.SipContact import SipContact
from sippy.UacStateTrying import UacStateTrying


from application.configuration import *
import getopt, sys, os

from twisted.python import syslog
from twisted.python.log import msg
from twisted.python.log import err

global_config = {}

class UserData:
	# List of [Int User Id, Ext Display Name, Ext Name, Ext Login, Ext Pasword, Ext SIP Domain, Ext Sip Port]
	Data = []
	Timer = None

	def __init__(self):
		self.Timer = LoopingCall(self.get_data)
		self.Timer.start(210, True)

	def get_data(self):
		# Obtain list of [Int User Id, Ext Display Name, Ext Name, Ext Login, Ext Pasword, Ext SIP Domain, Ext Sip Port] somehow
		#
		# For example, you could select them from DB, receive over network or just hardcode as in this example
		self.Data = [
			("internaluser",        "Registrar Agent",      "extacc1",      "extlogin1",    "extpass1",     "ext1.domain1.com",     "5060"),
			("internaluser",        "Registrar Agent",      "extacc2",      "extlogin2",    "extpass2",     "ext1.domain2.com",     None),
			("internaluser",        "Registrar Agent",      "extacc3",      "extlogin3",    "extpass3",     "ext1.domain3.com",     None)
			]

def recvConnect(ua, rtime, origin):
	msg("recvConnect %s" % str(ua))
	# Final 200 OK - clean up stuff here
	ua.event_cb = None
	ua.conn_cbs = None
	ua.disc_cbs = None
	ua.fail_cbs = None
	ua.dead_cbs = None
	ua.tr = None
	global_config['_sip_tm'].unregConsumer(ua, str(ua.cId))

def recvDisconnect(ua, rtime, origin, result = 0):
	msg("recvDisconnect %s" % str(ua))
	pass

def recvDead(ua):
	msg("recvDead %s" % str(ua))
	# Final auth failure - clean up stuff here
	ua.event_cb = None
	ua.conn_cbs = None
	ua.disc_cbs = None
	ua.fail_cbs = None
	ua.dead_cbs = None
	ua.tr = None
	global_config['_sip_tm'].unregConsumer(ua, str(ua.cId))


def recvEvent(event, ua):
	msg("recvEvent %s at %s" % (str(event), str(ua)))
	pass

def register_clients(ud):
	# For each record in UserData list create a registrar UA
	for (InternalUserId, ExtDisplayName, ExtName, ExtLogin, ExtPassword, ExtDomain, ExtPort) in ud.Data:
		print InternalUserId, ExtDisplayName, ExtName, ExtLogin, ExtPassword, ExtDomain, ExtPort
		Ua = UA(
				global_config,
				event_cb = recvEvent,
				username = ExtLogin,
				password = ExtPassword,
				conn_cbs = (recvConnect,),
				disc_cbs = (recvDisconnect,),
				fail_cbs = (recvDisconnect,),
				dead_cbs = (recvDead,),
				nh_address = (global_config['proxy_address'], global_config['proxy_port'])
			)

		if ExtPort == None:
			Ua.rTarget = SipURL(url = "sip:" + ExtName + "@" + ExtDomain)
			Ua.rUri = SipTo(body = "<sip:" + ExtName + "@" + ExtDomain + ">")
			Ua.lUri = SipFrom(body = ExtDisplayName + " <sip:" + ExtName + "@" + ExtDomain + ">")
		else:
			Ua.rTarget = SipURL(url = "sip:" + ExtName + "@" + ExtDomain + ":" + ExtPort)
			Ua.rUri = SipTo(body = "<sip:" + ExtName + "@" + ExtDomain + ":" + ExtPort + ">")
			Ua.lUri = SipFrom(body = ExtDisplayName + " <sip:" + ExtName + "@" + ExtDomain + ":" + ExtPort + ">")
		Ua.lUri.parse()
		Ua.lUri.genTag()
		Ua.lContact = SipContact(body = "<sip:" + InternalUserId + "@" + global_config['proxy_address'] + ">")
		Ua.routes = ()
		Ua.lCSeq = 1
		Ua.rCSeq = 1
		Ua.cId = SipCallId()
		req = Ua.genRequest("REGISTER")
		Ua.changeState((UacStateTrying,))
		global_config['_sip_tm'].regConsumer(Ua, str(Ua.cId))
		Ua.tr = global_config['_sip_tm'].newTransaction(req, Ua.recvResponse)

def recvRequest(req):
	if req.getMethod() in ('NOTIFY', 'INFO', 'PING'):
		return (req.genResponse(200, 'OK'), None, None)
	else:
		return (req.genResponse(501, 'Not Implemented'), None, None)

if __name__ == '__main__':
	syslog.startLogging('RegAgent')

	# Get config file
	configuration = ConfigFile('/etc/regagent/config.ini')

	global_config['proxy_address'] = configuration.get_setting('General', 'paddr', default='127.0.0.1', type=str)
	global_config['proxy_port'] = configuration.get_setting('General', 'pport', default=5060, type=int)
	global_config['_sip_address'] = configuration.get_setting('General', 'laddr', default='127.0.0.1', type=str)
	global_config['_sip_port'] = configuration.get_setting('General', 'lport', default=5060, type=int)
	global_config['sip_username'] = configuration.get_setting('General', 'username', default='username', type=str)
	global_config['sip_password'] = configuration.get_setting('General', 'password', default='password', type=str)
	global_config['_sip_tm'] = SipTransactionManager(global_config, recvRequest)

	ud = UserData()

	lc = LoopingCall(register_clients, ud)
	lc.start(60)

	reactor.run(installSignalHandlers = 0)
