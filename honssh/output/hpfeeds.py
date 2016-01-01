from honssh import config
from hpfeeds_server import hpfeeds_server

from twisted.python import log

class Plugin():

    def __init__(self, cfg):
        self.cfg = cfg

    def start_server(self):
        log.msg('[PLUGIN][HPFEEDS] - hpfeeds DBLogger start')

        server	= self.cfg.get('hpfeeds', 'server')
        port	= self.cfg.get('hpfeeds', 'port')
        ident	= self.cfg.get('hpfeeds', 'identifier')
        secret	= self.cfg.get('hpfeeds', 'secret')
        return hpfeeds_server.hpclient(server, port, ident, secret)

    def set_server(self, server):
        self.server = server
   
    def connection_lost(self, sensor):
        log.msg('[PLUGIN][HPFEEDS] - publishing metadata to hpfeeds')
        
        sensor['session'].pop('log_location')
        for channel in sensor['session']['channels']:
            if 'class' in channel:
                channel.pop('class')
            if 'ttylog_file' in channel:
                fp = open(channel['ttylog_file'], 'rb')
                ttydata = fp.read()
                fp.close()
                channel['ttylog'] = ttydata.encode('hex')
                channel.pop('ttylog_file')
        log.msg("[PLUGIN][HPFEEDS] - sessionMeta: " + str(sensor))
        self.server.publish(hpfeeds_server.HONSSHSESHCHAN, **sensor)
       
    def login_successful(self, sensor):
        self.send_auth_meta(sensor)
    
    def login_failed(self, sensor):
        self.send_auth_meta(sensor)

    def send_auth_meta(self, sensor):
        auth = sensor['session']['auth']
        authMeta = {'sensor_name': sensor['sensor_name'], 'datetime': auth['date_time'],'username': auth['username'], 'password': auth['password'], 'success': auth['success']}
        log.msg('[PLUGIN][HPFEEDS] - authMeta: ' + str(authMeta))
        self.server.publish(hpfeeds_server.HONSSHAUTHCHAN, **authMeta)  
        
    def validate_config(self):
        props = [['hpfeeds','enabled']]
        for prop in props:
            if not config.checkExist(self.cfg,prop) or not config.checkValidBool(self.cfg, prop):
                return False
            
        #If hpfeeds is enabled check it's config
        if self.cfg.get('hpfeeds','enabled') == 'true':
            props = [['hpfeeds','server'], ['hpfeeds','identifier'], ['hpfeeds','secret']]
            for prop in props:
                if not config.checkExist(self.cfg,prop):
                    return False
            prop = ['hpfeeds','port']
            if not config.checkExist(self.cfg,prop) or not config.checkValidPort(self.cfg,prop):
                return False
        
        return True