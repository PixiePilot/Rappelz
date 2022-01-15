from ast import Str
from logging import currentframe
import threading
import os
import discord
from discord.client import Client
from discord.ext import commands
import time
from dotenv import load_dotenv
import pyodbc
import asyncio
import random
import hashlib
giveawaylist = []
md5key = str(2020)
connah = None # will later represent the connection to the Auth DB
conn = None # will later represent the connection to the Telecaster DB
connbil = None # Will later represent the connection to the Billing DB (Mainly used for paid item ( Cs box ) )
connectionstring = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Telecaster;'
                    'Trusted_Connection=yes;')

connectionstringah = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Auth;'
                    'Trusted_Connection=yes;')

connectionstringbil = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Telecaster;'
                    'Trusted_Connection=yes;')
#^ The connection strings ^


#loads the discord token.
with open("Token.txt") as read:
    DISCORD_TOKEN = (read.readline())

bot = commands.Bot(command_prefix="!")

#On_ready is code that's executed whenever the bot starts, In this case it will attempt to connect to the sql server.
print("Attempting to connect to the SQL server...")
@bot.event
async def on_ready():
    global conn,connah,connbil,connectionstring

    try:
        conn = pyodbc.connect(connectionstring)
        connah = pyodbc.connect(connectionstringah)
        connbil = pyodbc.connect(connectionstringbil)
    except ConnectionRefusedError:
        print('Connection refused by SQL server\nThis bot only works with Myssql make sure you\'re not using Mysql')
        quit()
    except ConnectionError:
        print('Unable to connect to SQL server\nThis could be caused by :\nIncorrect password or user or invalid permissions to see the error')
        quit()

    print(f'successfully connected to SQL server.\nLogged in as user {bot.user} on discord')


#list of functions
def functionlvl(msg):
        cursor = conn.cursor()
        cursor.execute('SELECT TOP(3) name , lv from dbo.Character order by lv DESC')
        data    = cursor.fetchall()
        name    = []
        level   = []
        message = str()

        for row in data:
            name.append(row.name)
            level.append(row.lv)


        for rank, (namestring, levelstring) in enumerate(zip(name,level)):

            message = (f'{message}\nRank {rank+1}\nname : {namestring:10} level: {levelstring}')
        message = (f'```{message}```')
        return message
#Funciton level is simply the function that shows the top 3 highest level players in the game and returns the value

def functiongold(msg):
    cursor = conn.cursor()
    cursor.execute('SELECT TOP(3) name , gold from dbo.Character order by gold DESC')
    data = cursor.fetchall()
    name = []
    gold = []
    message = str()

    for row in data:
        name.append(row.name)
        gold.append(row.gold)

    for rank, (namestring, goldstring) in enumerate(zip(name, gold)):

        message = (f'{message}\nRank{rank+1:3}\n name: {namestring:10} ruppee: {goldstring:3}')

    message = f'```{message}```'
        
    return message
#Funciton gold is simply the function that shows the top 3 richest players in the game and returns the value

def discordidtoname(msg):
        cursor = connah.cursor()
        user = msg.author.id
        cursor.execute(f"SELECT account,DiscordID FROM [Account] WHERE DiscordID ={user}")
        result = cursor.fetchall()
        username = []
        count = 0

        for row in result:
            username.append(row.account)
            count += 1
            if count >= 2:
                msg.channel.send("You can only have one discord ID per account.")
                return False
        username = username.pop()
        return username

def discordidtonamegiveaway(msg,id):
        cursor = connah.cursor()
        user = id
        cursor.execute(f"SELECT account_id,DiscordID FROM [Account] WHERE DiscordID ={user}")
        result = cursor.fetchall()
        accountid = []
        count = 0 
        for row in result:
            count +=1
            if count >= 2:
                return
            accountid.append(row.account_id)


        accountid = accountid.pop()
        return accountid
#Function to resolves the users account based on their discord ID ( Needs the ID to already be added to the AUTH db table design in varchar ( it's used as an int ) )

def md5hasher(md5key:Str,login:Str):
    loginstr = (md5key+login)
    result = hashlib.md5(loginstr.encode())
    hashedlogin = (result.hexdigest())
    return hashedlogin
#Md5hash for passwords in Rappelz, It takes in a md5key + password and returns both of those hashed

async def taskwinner(waittime,msg,giveawaylist,id):
    global connbil
    connbil = connbil.cursor()
    await asyncio.sleep(waittime)
    print(giveawaylist)
    amount = len(giveawaylist)
    randomnumber = random.randint(0,amount)
    randomnumber -= 1
    winner = giveawaylist[randomnumber]
    winner = discordidtonamegiveaway(msg,winner)
    print(winner)
    # After learning billing insert query here 
    return
#Timer for giveaway after deletion, Since it's a multithread the sleep will not stop the rest of the code

@bot.command()
async def lvl(msg):
    message = functionlvl(msg)
    await msg.channel.send(message)
#functionlvl

@bot.command()
async def gold(msg):
    message = functiongold(msg)
    await msg.channel.send(message)
#functiongold

@bot.command()
async def test(msg):
    resolved_name = discordidtoname(msg)
    await msg.channel.send(resolved_name)
#function discordidtoname

@bot.command()
async def giveaway(msg,itemname: str,timer: int,id: int, timetype: str):
        global giveawaymessage,giveawaylist
        giveawaymessage = await msg.channel.send((f'There\'s a give away where {itemname} will be given away in {timer} seconds'))
        emoji = '\N{THUMBS UP SIGN}'
        await giveawaymessage.add_reaction(emoji)
        print(giveawaymessage)
        taskdelmsg = asyncio.create_task(taskwinner(timer,msg,giveawaylist,id))        
        await giveawaymessage.delete(delay=timer)
        await taskdelmsg

@bot.command()
async def register(msg):
    
    await msg.channel.send(f"Please check your DM, {msg.author.name}")
    message = (f"Hello, {msg.author.name}.\nusing the DM's you will be able to savely link your discord to your Ingame account, Be wary though you can only have 1 ingame account connected to 1 discord account.\n By typing !link you will be able to link your discord account to Rappelz however you need to login first\nwhich can be done by typing !link in the following manner: !link loginname password")
    await msg.author.send(message)
    
#To do fix spamming !link on the same account
@bot.command()
@commands.dm_only()
async def link(msg,user:str,login:str):
    global connah,md5key
    cursor = connah.cursor()
    
    hashedlogin = md5hasher(str(md5key),login)
    userSQL = "'"+user+"'"
    hashedloginSQL = "'"+hashedlogin+"'"
    #^ Md hash, Rappelz requires you to use a MD5 hash and key you simply add those together and hash it then it's the same as in the database
    print(f"{user},{hashedlogin} has been called to verify by user {msg.author} their discord id is: {msg.author.id}")

    cursor.execute(f"SELECT account , password , DiscordID, account_id FROM [Account] WHERE (account = {userSQL} AND password = {hashedloginSQL})")

    logininfo = cursor.fetchall()
    account_id = None
    for row in logininfo:
        print(row)
        account_id = (row.account_id)
        account = (row.account)
        print("Account name: "+(row.account) +" Password: "+ (row.password)+" DiscordID: " +(row.DiscordID))


    if account_id == None:
        embed=discord.Embed(title="Login unsuccessful.", description="Either the username or password is incorrect", color=0xff0000)
        embed.set_author(name="Bot provided by Lyza")
        embed.set_thumbnail(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlNSlb7_KRQmYZ_vJu5u6sUfpqNwnGBxWuSB-au-XoeHk8NFkMad5ITes8RNEyRjsoJXw&usqp=CAU")
        embed.set_footer(text="Bot provided by Lyza")
        await msg.channel.send(embed=embed)
        return
    else:
        pass


    try:
        cursor.execute(f'UPDATE Account SET DiscordID = {msg.author.id} WHERE account_id = {account_id}')
    except:
        await msg.channel.send('Something went wrong, please try again if this issue persists contact the support team.')
        return
    cursor.commit()

    print(f'User {msg.author} has successfully logged into account {account} ID: {account_id}')
    embed=discord.Embed(title="Login successful!", description="You've successfully added your discord account to your Rappelz account", color=0x00ff40)
    #embed.set_author(name="Lyza's bot")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/794704213741535253/931914909011292190/9k.png")
    embed.add_field(name=f"Name: {msg.author.name}", value=f"ID: {msg.author.id}", inline=True)
    embed.add_field(name="Account", value=f"{account}", inline=True)
    embed.set_footer(text=f"Bot provided by Lyza")
    await msg.channel.send(embed=embed)
#The function to link your discord to the database

@bot.event
async def on_reaction_add(reaction,user):
    global giveawaymessage,giveawaylist
    if user.id == 921459290273898507:
        return
    if reaction.message == giveawaymessage:
        for check in giveawaylist:
            if check == user.id:
                return
        giveawaylist.append(user.id)
        print(giveawaylist)
    return
#Checks the current give away message for newly added ( does not save if bot shuts down)
bot.run(DISCORD_TOKEN)
