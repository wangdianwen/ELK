# /usr/bin/env python
#-*-coding=utf-8-*-

import os,sys,configparser


cf = configparser.ConfigParser()
cf.read("elk.ini")

agentIp = cf.get("AGENT","REMOTELOCATION").split(",")
logservername = cf.get("EKL","LSNAME")

# 创建服务端和客户端的logstash文件
REDISHOST = cf.get("REDIS","HOST")
REDISPORT = cf.get("REDIS","PORT")
REDISKEY  = cf.get("REDIS","KEY")

ESHOST = cf.get("EKL","ESHOST")
REMOTELOGPATH = cf.get("AGENT","REMOTELOGPATH")


logstash_agent = '\n\
input {\n\
	file {\n\
		path 	=> "REMOTELOGPATH"\n\
		type 	=> "ykLog"						# This format tells logstash to expect ‘logstash’ json events from the file.\n\
		format	=> json_event\n\
	}\n\
}\n\
\n\
output {\n\
	redis {\n\
		host 		=> "REDISHOST"\n\
		port 		=> REDISPORT\n\
		data_type 	=> "list"\n\
		key 		=> "REDISKEY"\n\
	}\n\
}\n\
'
logstash_agent = logstash_agent.replace('REDISHOST',REDISHOST)
logstash_agent = logstash_agent.replace('REDISPORT',REDISPORT)
logstash_agent = logstash_agent.replace('REDISKEY',REDISKEY)
logstash_agent = logstash_agent.replace('ESHOST',ESHOST)

logstash_server = '\n\
input {\n\
\n\
	redis {\n\
		host 		=> "REDISHOST"			# these settings should match the output of the agent\n\
		data_type	=> "list"\n\
		key 		=> "REDISKEY"\n\
		port 		=> REDISPORT			# We use the ‘json’ codec here because we expect to read # json events from redis.\n\
		codec 		=> json\n\
	}\n\
}\n\
\n\
filter {\n\
  if [type] == "ykLog" {\n\
	  grok {\n\
		match => [ "message","%{WORD:level} %{URIPATH:server} %{NUMBER:retcode} %{DATESTAMP_EVENTLOG:timestamp}" %{NUMBER:cost} ]\n\
	  }\n\
	  date {\n\
	  	match => [ "timestamp" , "yyyyMMddHHmmss"]\n\
	  	remove_field => ["timestamp" , "path"]\n\
	  }\n\
  }\n\
}\n\
\n\
output {\n\
\n\
	stdout {\n\
		codec			=> json\n\
	}\n\
\n\
	elasticsearch {\n\
		host			=> "ESHOST"\n\
		protocol		=> "http"\n\
	}\n\
}\n\
'
logstash_server = logstash_server.replace('REDISHOST',REDISHOST)
logstash_server = logstash_server.replace('REDISPORT',REDISPORT)
logstash_server = logstash_server.replace('REDISKEY',REDISKEY)
logstash_server = logstash_server.replace('ESHOST',ESHOST)


# 下载软件包,并且解压缩
os.popen('cd /usr/local/src; wget --no-check-certificate https://download.elasticsearch.org/logstash/logstash/logstash-1.4.2.tar.gz')
os.popen('cd /usr/local/src; wget --no-check-certificate https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.4.2.tar.gz')
os.popen('cd /usr/local/src; wget --no-check-certificate https://download.elasticsearch.org/kibana/kibana/kibana-4.0.0-beta3.tar.gz')
os.popen('cd /usr/local/src; tar zxfv logstash-1.4.2.tar.gz')
os.popen('cd /usr/local/src; tar zxfv elasticsearch-1.4.2.tar.gz')
os.popen('cd /usr/local/src; tar zxfv kibana-4.0.0-beta3.tar.gz')

# 移动软件到相关目录
os.popen('cd /usr/local/src; mv logstash-1.4.2 /usr/local/logstash')
os.popen('cd /usr/local/src; mv kibana-4.0.0-beta3 /usr/local/kibana')
os.popen('cd /usr/local/src; mv elasticsearch-1.4.2 /usr/local/elasticsearch')


# 创建服务端和客户端的文件
fp = open('/usr/local/logstash/' + logservername + '_server.conf' , 'w+')
fp.write( logstash_server );
fp.close()

fp = open('/usr/local/logstash/' + logservername + '_agent.conf' , 'w+')
fp.write( logstash_agent );
fp.close()

# 启动elasticsearch
os.popen('cd /usr/local/elasticsearch/bin/; ./elasticsearch -d')

# 启动kibana
os.popen('cd /usr/local/kibana/bin/; ./kibana -q &')

# 配置logstash
os.popen('cd /usr/local/logstash/bin/; ./logstash -f  ' + logservername + '_server.conf &')


# 配置客户端的logstash,并且启动
for ip in agentIp:
	tmp		= ip.split(':')
	user	= tmp[0]
	ip		= tmp[1]
	port	= tmp[2]
	# 传代码
	os.popen('scp -P ' + port + ' -r /usr/local/logstash/ ' + user + '@' + ip + '/user/local/')

	os.popen('ssh -p ' + port + ' ' + user + '@' + ip + ' /usr/local/logstash/bin/logstash -f /usr/local/logstash/' + logservername + '_agent.conf &')



def clearIndex( days = 30 ):
	url = 'http://localhost:9200/logstash-';
	# 每次只删除一天的
	#delurl = url + 






