#!/usr/bin/python3

import discord
import asyncio
import re

from dse.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from dse.auth import PlainTextAuthProvider

#Configuration
contactpoints = ['66.70.191.99']
auth_provider = PlainTextAuthProvider (username='travian', password='Password123')

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
    relaychan = discord.Object(id='506599354413350912')
    #relaychan = message.channel
    if message.author == client.user:
        return
    if message.content.startswith('!test'):
        msg = "Hello, <@%s>" % (message.author.id)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!send'):
        print("!send")
        input = message.content.split()
        if len(input) != 6:
            await client.send_message(message.channel, 'Usage: !send <reqid> <wood> <clay> <iron> <crop>')
            return
        reqid = str(input[1])
        wood = str(input[2])
        clay = str(input[3])
        iron = str(input[4])
        crop = str(input[5])
        query = """ INSERT INTO travian.requests (reqid, status) VALUES (%s, 'open') """ % (int(reqid))
        print(query)
        session.execute (query)
        query = """ select reqid, wood, woodsent, clay, claysent, iron, ironsent, crop, cropsent, player, village from travian.requests WHERE reqid = %s """ % (reqid)
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

client.run('NTEwMTI1NDEwNTYzMTI5MzQ1.DsYFkA.8PjeWYzliKkbZoEmclIMe4PlGXY')
