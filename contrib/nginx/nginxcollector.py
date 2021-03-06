# Copyright (C) 2010-2011 by Brightcove Inc. 
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

# To enable the nginx status page to work with defaults,
# add a file to /etc/nginx/sites-enabled/ (on Ubuntu) with the
# following content:
#   server {
#       listen 127.0.0.1:8080;
#       server_name localhost;
#       location /nginx_status {
#           stub_status on;
#           access_log /data/server/shared/log/access.log;
#           allow 127.0.0.1;
#           deny all;
#       }
#   }

import urllib2
import re

import diamond.collector 

class NginxCollector(diamond.collector.Collector):
    """
    Collect statistics from Nginx
    """
    
    def get_default_config(self):
        default_config = {}
        default_config['req_host'] = 'localhost'
        default_config['req_port'] = 8080
        default_config['req_path'] = '/nginx_status'
        default_config['path'] = 'nginx'
        return default_config

    def collect(self):
        activeConnectionsRE = re.compile(r'Active connections: (?P<conn>\d+)')
        totalConnectionsRE = re.compile('^\s+(?P<conn>\d+)\s+(?P<acc>\d+)\s+(?P<req>\d+)')
        connectionStatusRE = re.compile('Reading: (?P<reading>\d+) Writing: (?P<writing>\d+) Waiting: (?P<waiting>\d+)')
        metrics = []
        req = urllib2.Request('http://%s:%i%s' % (self.config['req_host'], int(self.config['req_port']), self.config['req_path']))
        try:
            handle = urllib2.urlopen(req)
            for l in handle.readlines():
                l = l.rstrip('\r\n')
                if activeConnectionsRE.match(l):
                    self.publish('active_connections', int(activeConnectionsRE.match(l).group('conn')))
                elif totalConnectionsRE.match(l):
                    m = totalConnectionsRE.match(l)
                    req_per_conn = float(m.group('req')) / float(m.group('acc'))
                    self.publish('conn_accepted', int(m.group('conn')))
                    self.publish('conn_handled', int(m.group('acc')))
                    self.publish('req_handled', int(m.group('req')))
                    self.publish('req_per_conn', float(req_per_conn))
                elif connectionStatusRE.match(l):
                    m = connectionStatusRE.match(l)
                    self.publish('act_reads', int(m.group('reading')))
                    self.publish('act_writes', int(m.group('writing')))
                    self.publish('act_waits', int(m.group('waiting')))
        except IOError, e:
            self.log.error("Unable to open http://%s:%i:%s" % (self.config['req_host'], int(self.config['req_port']), self.config['req_path']))
        except Exception, e:
            self.log.error("Unknown error opening url: %s" % (e))
