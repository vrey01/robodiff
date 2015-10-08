#!/usr/bin/env python

""" 
 RoboDiff.py

 python code to control ESRF RoboDiff device

 (c) ESRF

""" 
__version__ = "0.1"

import asyncore
import socket
import gevent

import logging
import time
import os
import sys

progname = os.path.basename( sys.argv[0] )

debuglevel = logging.ERROR  # you can change to DEBUG with -d option

logging.basicConfig(level=debuglevel, \
     format="%s"%progname + "%(levelname)8s %(message)s")

log = logging.getLogger()

class RobotSocket(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)

        self.host = host 
        self.port = port 

	self.terminator = ";"
        self.cmd_buffer = ''

	self._cmd_no = 0
	self._read_no = 0
	self._latest = None
	self.last_read_time = 0
	self.cmd_pending = False

        self.closed = True

        self.reconnect()

    def reconnect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))   

    def handle_connect(self):
        log.debug("Connected to server: %s" % self.name)
	self.settimeout(0.1)
        conn_msg = self.get_read()
	log.debug(" - conn message: %s" % conn_msg)
	self.settimeout(2)
	if conn_msg:
            log.debug(" - connected now")
	    self.closed = False
        else:
	    self.closed = True

    def handle_close(self):
        self.close()
        self.closed = True

    def send_command(self,cmd, wait=False):
        if self.closed:
	    return None
        self.cmd_buffer = cmd + self.terminator
        self._cmd_no += 1
	self._latest = cmd
	log.debug("sending command %s" % cmd)
	self.cmd_pending = True
	if wait:
	   self._wait()  
	   return self._answer
        else:
	   return self._cmd_no

    def cmd_state(self):
        return self.cmd_pending

    def writable(self):
	return (len(self.cmd_buffer) > 0)

    def handle_write(self):
        if self._latest != "Status":
            log.debug("send command out (%s) : %s " % (self.name, self.cmd_buffer))
        sent = self.send(self.cmd_buffer)
        self.cmd_buffer = self.cmd_buffer[sent:]
	self.cmd_pending = False

    def handle_read(self):
        self._answer = self.get_read()
        #self._answer = self.recv(4096)
        self._waitanswer = False
	self._read_no += 1

    def get_read(self):
        try: 
            return self.recv(4096)
        except socket.timeout: 
	    log.debug("Timeout reading")
            return None

    def get_cmd_result(self,cmdid):
	log.debug("Reading result for %s read_no is %s" % (cmdid, self._read_no))
        if cmdid == self._read_no:
           return self._answer
	else:     
           return None

    def _wait(self):
       self._waitanswer = True
       while self._waitanswer:
           asyncore.loop(timeout=0.1, count=1)

class RobotService(RobotSocket):

    name = "robot_service"

    def __init__(self, host, port):

        RobotSocket.__init__(self,host,port)

        self.state = 10 # invented... meaning there was no state information in status string
	self.power = "notinit"
	self.robot = "notinit"
	self.speed = "notinit"
        self.status = "disconnected"
	self.status_cmd = "Status"
	self.kill_cmd = "Stop"
	self.motor_positions = {}

    def check_status(self):
        if self.closed:
	    log.debug("reconnecting")
            self.reconnect()

	if time.time() - self.last_read_time < 0.01:
             if self._cmd_no > self._read_no:
	         return
        else:
	    self._read_no = self._cmd_no

        self.send_command(self.status_cmd, wait=True)

    def kill_task(self):
        if self.closed:
            self.reconnect()

        if self._waitanswer:
            log.debug("(service socket) reading pending answer for (%s) before stopping task" % (self._latest))
            _answer = self.get_read()
            #_answer = self.recv(4096)
        self.send_command(self.kill_cmd, wait=True)

    def handle_read(self):
        self._answer = self.get_read()
        #self._answer = self.recv(4096)

        log.debug("(service socket) answer for (%s) got --%s--" % (self._latest, self._answer))
        if self._answer and self._latest is self.status_cmd:
	    self._status = self._answer
            self.parse_status()
	    self.state_read = True
	else:      
	    pass
            #log.debug("(service socket) answer for (%s) got --%s--" % (self._latest, self._answer))

        self._waitanswer = False
	self._read_no += 1
	self.last_read_time = time.time()

    def _wait(self):
       self._waitanswer = True

       while self._waitanswer:
           asyncore.loop(timeout=0.1, count=1)

    def parse_status(self):

        parts = self._status.split(";")

        self.state = 10 # invented... meaning there was no state information in status string

        self.status = parts[0]

	self.motor_positions = {}

        for part in parts[1:]:

            components = part.split(" ")
            subsys = components[0]

            if subsys == "task":
               self.task = components[1]
	       try:
                  self.state = int(components[2])
	       except:
	          log.debug("Error parsing task state %s" % part)
		  self.state = 10
	    elif subsys == "robot":    
               self.robot = components[1]
	    elif subsys == "power":    
               self.power = components[1]
	    elif subsys == "speed":    
               self.speed = components[1]
	    elif subsys.startswith("pos"):
	       _motname = components[1]
	       _motpos = components[2]
	       self.motor_positions[_motname] = _motpos

    def get_state(self,force=False):
        if force:
	    self._wait()
        return self.state

    def get_power(self):
        return self.power

    def get_speed(self):
        return self.speed

    def get_robot(self):
        return self.robot

    def get_motors(self):
        return self.motor_positions[keys]

    def get_position(self, axe):
        if axe in self.motor_positions:
	    return self.motor_positions[axe]
	else:       
	    return None

class RobotCommand(RobotSocket):

    name = "robot_cmd"

    def __init__(self, host, port):
        RobotSocket.__init__(self,host,port)
	self.cmd_sent = False

    def handle_read(self):
	self._answer = self.get_read()
	#self._answer = self.recv(4096)
        log.debug("(command socket) read (%s) got %s" % (self.name, self._answer))
        self._waitanswer = False
	self._read_no += 1

class RoboDiff:

    cmds = {
       "id":  "IdRobot:taskId()",
       "enable":  "enablePower()",
       "disable":  "disablePower()",
    }
    status_refresh_rate = 0.05
 
    def __init__(self, host, portserv, portcmd):
        self.host = host
        self.portserv = portserv
        self.portcmd = portcmd
        self.running = False
        self.cmd_conn = RobotCommand(self.host, self.portcmd)
        self.service_conn = RobotService(self.host, self.portserv)
	self.need_one_read = False
 
    # change these so that service_conn is updating and the latest info is reported
    #  without reading again
    def get_state(self):
	cmd_state = self.cmd_conn.cmd_state()

	if cmd_state:
	    log.debug("command pending")
	    self.need_one_read = True
            return 1	 

        state = self.service_conn.get_state(force=self.need_one_read)
	self.need_one_read = False
	return state
 
    def get_power(self):
        return self.service_conn.get_power()

    def get_robot(self):
        return self.service_conn.get_robot()

    def get_speed(self):
        return self.service_conn.get_speed()

    def get_position(self,motor):
        return self.service_conn.get_position(motor)

    def get_motors(self):
        return self.service_conn.get_motors()
    #  
 
    def switchpower(self):
        if self.get_power() == "disable": 
	    self.enable_power()
	else:     
	    self.disable_power()

    def enable_power(self):
        self.exec_command( self.cmds["enable"], wait=False )

    def disable_power(self):
        self.exec_command( self.cmds["disable"], wait=False )
    
    def get_id(self):
        return self.exec_command( self.cmds["id"] )

    def stop(self):
        # send stop command on service socket
        return self.service_conn.kill_task()

    def exec_command(self,cmd, wait=True):
 
        if not self.running:
            self.run()

	self.cmd_conn.cmd_sent = False
        cmdid = self.cmd_conn.send_command(cmd)
	self.need_one_read = True

        if wait:
            self.waitdone()
            return self.cmd_conn.get_cmd_result(cmdid)
        else:
            return cmdid
 
    def get_cmd_result(self,cmdid):
        return self.cmd_conn.get_cmd_result(cmdid)

    def update(self):
        while True:
            status = self.service_conn.check_status()
            gevent.sleep(self.status_refresh_rate)

    def run(self):
        self.running = True
        gevent.spawn( self.update )
	gevent.sleep(0.2)

    def loop(self):
        while asyncore.socket_map:
            asyncore.loop(timeout=0.1, count=1)
            gevent.wait(timeout=0.01)

    def sync(self):
        if self.service_conn.closed:
	    return
        asyncore.loop(timeout=0.1, count=1)
        gevent.wait(timeout=0.01)

    def waitdone(self,timeout=None):

        t0 = time.time()

        while True:
            if self.get_state() != 1:
	       break

            gevent.sleep(0.05)

            if timeout and (time.time() -t0  > timeout):
	        log.error("timeout")
	        break

def getVersion():
    return __version__

