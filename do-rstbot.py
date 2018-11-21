#!/usr/bin/python3

import discord
import asyncio
import re

from dse.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from dse.auth import PlainTextAuthProvider

#Configuration
contactpoints = ['6.7.11.9']
auth_provider = PlainTextAuthProvider (username='travian', password='sdfsdfgsdf')

cluster = Cluster( contact_points=contactpoints,
                   auth_provider=auth_provider
                   )

session = cluster.connect()

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    #relaychan = discord.Object(id='dfgsdgsdf')
    relaychan = message.channel
    if message.author == client.user:
        return
    if message.content.startswith('!test'):
        msg = "Hello, <@%s>" % (message.author.id)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!status'):
        print("!status")
        input = message.content.split()
        if len(input) != 2:
            await client.send_message(message.channel, 'Usage: !status <reqid>')
            return
        reqid = input[1]
        query = """ select reqid, wood, woodsent, clay, claysent, iron, ironsent, crop, cropsent, player, village, status from travian.requests WHERE reqid = %s """ % (reqid)
        results = session.execute (query)
        for row in results:
            reqid = row[0]
            wood = row[1]
            woodsent = row[2]
            clay = row[3]
            claysent = row[4]
            iron = row[5]
            ironsent = row[6]
            crop = row[7]
            cropsent = row[8]
            player = row[9]
            village = row[10]
            status = row[11]
            xy = village.split(',')
            msg = """ReqID: %s/%s Player: %s (https://ts1.travian.us/karte.php?x=%s&y=%s)\n Wood: %s/%s\n Clay: %s/%s\n Iron %s/%s\n Crop: %s/%s  """ % (reqid, status, player, xy[0], xy[1], woodsent, wood, claysent, clay, ironsent, iron, cropsent, crop)
            await client.send_message(message.channel, msg)

    elif message.content.startswith('!list'):
        print("!list")
        input = message.content.split()
        query = """SELECT player, xy, name FROM travian.villages WHERE player = '%s'""" % (message.author.id)
        results = session.execute (query)
        msg = ""
        for row in results:
            msg = msg + "\n" + row[1] + " " + row[2]
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!del'):
        print("!del")
        input = message.content.split()
        if len(input) != 2:
            await client.send_message(message.channel, 'Usage: !del <village x,y>')
            return 
        village = str(input[1])
        village = re.sub('[\(\)\{\}<>]', '', village)
        xy = village.split(',')
        if len(xy) != 2:
            xy = village.split('|')
        if len(xy) != 2:
            await client.send_message(message.channel, 'Invalid village coordinates!')
            return
        xy = village.split(',')
        village = str(xy[0]) + "," + str(xy[1])
        player = message.author.id
        query = """DELETE FROM travian.villages WHERE player = '%s' AND xy = '%s'""" % (player, village)
        session.execute (query)
        msg = """Deleted %s""" % (village)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!add'):
        print("!add")
        input = message.content.split()
        if len(input) < 2:
            await client.send_message(message.channel, 'Usage: !add <village x,y> <name>')
            return
        village = str(input[1])
        village = re.sub('[\(\)\{\}<>]', '', village)
        xy = village.split(',')
        if len(xy) != 2:
            xy = village.split('|')
        if len(xy) != 2:
            await client.send_message(message.channel, 'Invalid village coordinates!')
            return
        xy = village.split(',')
        village = str(xy[0]) + "," + str(xy[1])
        player = message.author.id
        input.pop(0)
        input.pop(0)
        name = ""
        for n in input:
            name = name + " " + n
        query = """ INSERT INTO travian.villages (player, xy, name) VALUES ('%s', '%s', '%s') """ % (player, village, name)
        session.execute (query)
        msg = """Added %s (%s)""" % (name, village)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!send'):
        print("!send")
        input = message.content.split()
        if len(input) != 6:
            await client.send_message(message.channel, 'Usage: !send <reqid> <wood> <clay> <iron> <crop>')
            return
        reqid = int(input[1])
        swood = int(input[2])
        sclay = int(input[3])
        siron = int(input[4])
        scrop = int(input[5])
        query = """ INSERT INTO travian.requests (reqid, status) VALUES (%s, 'open') """ % (reqid)
        session.execute (query)
        query = """ select reqid, wood, woodsent, clay, claysent, iron, ironsent, crop, cropsent, player, village from travian.requests WHERE reqid = %s """ % (reqid)
        results = session.execute (query)
        for row in results:
            reqid = row[0]
            wood = row[1]
            woodsent = row[2] + swood
            clay = row[3]
            claysent = row[4] + sclay
            iron = row[5]
            ironsent = row[6] + siron
            crop = row[7]
            cropsent = row[8] + scrop
            player = row[9]
            village = row[10]
            query = """ INSERT INTO travian.requests (reqid, woodsent, claysent, ironsent, cropsent) VALUES (%s, %s, %s, %s, %s) """ % (int(reqid), woodsent, claysent, ironsent, cropsent)
            session.execute (query)
            await client.send_message(message.channel, "Request updated!")

    elif message.content.startswith('!new'):
      try:
        query = """ select reqid, wood, clay, iron, crop, player, village from travian.requests WHERE solr_query = 'status:new' """
        results = session.execute (query)
        for row in results:
            reqid = row[0]
            wood = row[1]
            clay = row[2]
            iron = row[3]
            crop = row[4]
            player = row[5]
            village = row[6]
            xy = village.split(',')
            newmsg = """%s: <@%s> (%s/%s/%s/%s) https://ts1.travian.us/karte.php?x=%s&y=%s """ % (reqid, player, wood, clay, iron, crop, xy[0], xy[1]) 
            await client.send_message(message.channel, newmsg)
        await client.send_message(message.channel, "End of new requests")
      except:
        await client.send_message(message.channel, "No new requests")

    elif message.content.startswith('!closed'):
        print("!closed")
        query = """ select reqid, wood, clay, iron, crop, player, village from travian.requests WHERE solr_query = 'status:closed' """
        results = session.execute (query)
        for row in results:
            reqid = row[0]
            wood = row[1]
            clay = row[2]
            iron = row[3]
            crop = row[4]
            player = row[5]
            village = row[6]
            xy = village.split(',')
            newmsg = """%s: <@%s> (%s/%s/%s/%s) https://ts1.travian.us/karte.php?x=%s&y=%s """ % (reqid, player, wood, clay, iron, crop, xy[0], xy[1]) 
            await client.send_message(message.channel, newmsg)
        await client.send_message(message.channel, "End of closed requests")

    elif message.content.startswith('!close'):
        print("!close")
        input = message.content.split()
        if len(input) != 2:
            await client.send_message(message.channel, 'Usage: !close <reqid>')
            return
        reqid = input[1]
        query = """ INSERT INTO travian.requests (reqid, status) VALUES (%s, 'closed') """ % (int(reqid))
        session.execute (query)
        newmsg = """Request #%s has been closed.""" % (reqid)
        await client.send_message(message.channel, newmsg)

    elif message.content.startswith('!open'):
        print("!open")
        query = """ select reqid, wood, clay, iron, crop, player, village from travian.requests WHERE solr_query = 'status:open' """
        results = session.execute (query)
        for row in results:
            reqid = row[0]
            wood = row[1]
            clay = row[2]
            iron = row[3]
            crop = row[4]
            player = row[5]
            village = row[6]
            xy = village.split(',')
            newmsg = """%s: <@%s> (%s/%s/%s/%s) https://ts1.travian.us/karte.php?x=%s&y=%s """ % (reqid, player, wood, clay, iron, crop, xy[0], xy[1]) 
            await client.send_message(message.channel, newmsg)

    elif message.content.startswith('!res'):
        input = message.content.split()
        if len(input) != 6:
            await client.send_message(message.channel, 'Usage: !res <wood> <clay> <iron> <crop> <village x,y OR (x|y)>')
            await client.send_message(message.channel, 'ie: !res 1000 0 2000 1000 10,-10')
            await client.send_message(message.channel, 'ie: !res 1000 0 2000 1000 (10|-10)')
            return
        wood = str(input[1])
        clay = str(input[2])
        iron = str(input[3])
        crop = str(input[4])
        village = str(input[5])
        village = re.sub('[\(\)\{\}<>]', '', village)
        xy = village.split(',')
        if len(xy) != 2:
            xy = village.split('|')
        if len(xy) != 2:
            await client.send_message(message.channel, 'Incorrect village coordinates!')
            await client.send_message(message.channel, 'ie: !res 1000 0 2000 1000 10,-10')
            return
        village = xy[0] + "," + xy[1]

        query = """ UPDATE travian.counts set count = count + 1 where key = 'reqid' """ 
        session.execute (query)
        query = """ select count from travian.counts where key = 'reqid' """ 
        results = session.execute (query)
        reqid = str(results[0][0])
        
        query = """ INSERT INTO travian.requests (reqid, player, wood, clay, iron, crop, village, status, woodsent, claysent, ironsent, cropsent) VALUES (%s, '%s', %s, %s, %s, %s, '%s', 'new', 0, 0, 0, 0) """ % (int(reqid), message.author.id, wood, clay, iron, crop, village)
        print(query)
        session.execute (query)

        relay = "(%s) <@%s> has requested to https://ts1.travian.us/karte.php?x=%s&y=%s: \n  Wood: %s\n  Clay: %s\n  Iron: %s\n  Crop: %s" %(reqid, message.author.id, xy[0], xy[1],wood, clay, iron, crop)
        awknowledge = "<@%s>, request #%s has been submitted" %(message.author.id, reqid)
        await client.send_message(relaychan, relay)
        await client.send_message(message.channel, awknowledge)
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')

client.run('sdfsdfasdfsdfaDsdfsdfasdfsdfasdfsdfasdfsdfsdfsdfa')
