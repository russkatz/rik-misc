#from sopel import module
import sopel
import requests
import time
import calendar
import json
from random import randint
from sopel.module import commands, event, rule
chanmin = 15
chandelay = 10
whoisdelay = 10
resetdelay = 21600
chanurl = 'http://127.0.0.1:4001/incoming/chan'
infourl = 'http://127.0.0.1:4001/incoming/info'
NETWORK = "undernet"

#BOT Startup Logic
chanlist = []
chanqueue = set([])
nicklist = []
nickqueue = set([])
chantimer = calendar.timegm(time.gmtime())
whoistimer = calendar.timegm(time.gmtime())
resettimer = calendar.timegm(time.gmtime())

#Bot Running Logic
def queue_whois(bot, nick):
    global nicklist
    known = 0
    nick = nick.replace("@","")
    nick = nick.replace("+","")
    for n in nicklist:
       if(nick == n):
          known = 1
    else:
       print("QUEUEING: %s") % nick
       nicklist += [nick]
       nickqueue.add(nick)

def send_names(bot, channel):
    """
    Sends the NAMES command to the server for the
    specified channel.
    """
    bot.write(["NAMES", channel])

def check_chan(bot, channel):
    """
    new channel auto join logic
    """
    global chanlist
    global chanqueue
    known = 0
    for c in chanlist:
        if(channel == c):
           known = 1
    if(known == 0):
       print("New channel %s found, queueing!") % channel
       chanlist += [channel]
       chanqueue.add(channel)

@event('319')
@rule('.*')
def whois_channels_found(bot, trigger):
    """
    Whois Channel Info
    """
    global chanurl
    list1 = trigger.raw.split(":")
    channels = list1[2]
    clist = channels.split()
    list1 = trigger.raw.split()
    nick = list1[3]
    for c in clist:
        l = c.split("#")
        mode = l[0]
        channel = l[1].replace("'","")
        cname = "#" + channel
	check_chan(bot,cname)
        payload = {'network': NETWORK, 'nick': nick, 'channel': channel, 'mode': mode}
        ##print(payload)
        r = requests.post(chanurl, json=payload)

@event('353')
@rule('.*')
def names_found(bot, trigger):
    """
    NAMES response
    """
    print("NAMES response")
    print(trigger.raw)
    list1 = trigger.raw.split(":")
    list2 = trigger.raw.split()
    names = list1[2].split()
    channel = list2[4]
    print("people in %s: %s") % (channel, len(names))
    ##print("sending whois")
    for i in names:
       n1 = i.replace("@", "")
       n2 = n1.replace("+", "")
       #print("CHECKING: %s") % n2
       queue_whois(bot, n2)
    #print(len(names), chanmin)
    if(len(names) < chanmin):
       print("Parting %s") % channel
       bot.part(channel)
    else:
       print("staying in %s") % channel


@event('311')
@rule('.*')
def whois_info_found(bot, trigger):
    """
    Whois User info
    """
    global infourl
    list1 = trigger.raw.split(":")
    list2 = trigger.raw.split()
    realn = list1[2].replace("'","")
    nick = list2[3]
    identd = list2[4]
    hostname = list2[5]
    payload = {'network': NETWORK, 'nick': nick, 'identd': identd, 'hostname': hostname, 'realname': realn}
    ##print(payload)
    r = requests.post(infourl, json=payload)

@event('JOIN')
@rule('.*')
def on_join_whois(bot, trigger):
    """
    Trigger on join
    """
    l1 = trigger.raw.split()
    channel = l1[2]
    if(bot.nick == trigger.nick):
        send_names(bot, channel)
        print("bot has joined: %s") % channel
    queue_whois(bot, trigger.nick)

@sopel.module.interval(1)
def whois_timer(bot):
   global nickqueue
   global whoisdelay
   global whoistimer
   if((whoisdelay + whoistimer)<calendar.timegm(time.gmtime())):
      print("Nicks in Queue: %s") % len(nickqueue)
      n = ""
      for n in nickqueue:
         print("WHOIS: %s") % n
         bot.write(["WHOIS", n])
         nickqueue.remove(n)
         break
      whoistimer = calendar.timegm(time.gmtime())

@sopel.module.interval(1)
def chan_join_timer(bot):
   global chanqueue
   global chandelay
   global chantimer
   if((chandelay + chantimer)<calendar.timegm(time.gmtime())):
      c = ""
      for c in chanqueue:
         print("Channels in Queue: %s") % len(chanqueue)
         print("JOINING: %s") % c
         bot.join(c)
         chanqueue.remove(c)
         break
      chantimer = calendar.timegm(time.gmtime())

@sopel.module.interval(1)
def reset_timer(bot):
   global chanqueue
   global resettimer
   global resetdelay
   global chanlist
   global nicklist
   if((resetdelay + resettimer)<calendar.timegm(time.gmtime())):
      print("RESETTING KNOWN ENTITES!")
      chanlist = []
      nicklist = []
      for c in bot.channels:
         print("RESET PARTING: %s") % c
         bot.part(c)
      resettimer = calendar.timegm(time.gmtime())
