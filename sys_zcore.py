#! /usr/bin/python3
# Mode60 Ultra-beta ZeroOne
# ======================================================================================================================
# Title.............: 'zcore'
# Filename..........: sys_zcore.py (system module)
# Version...........: 0.1x
# Author............: Neo Nemesis
# Description.......: zcore system module (includes basic IRC operations/features)
#                   : this also holds importable tools and functions for plugins
# Remarks...........: This is the prototype build structure of a system module.
# Author Notes......: This is likely to change unexpectedly, and get expanded and improved
# ======================================================================================================================
# Imports...........:
from configparser import ConfigParser
from datetime import date
from datetime import datetime
import configparser
import socket
import asyncio
import time
import os.path
import logging
import random
# ======================================================================================================================
# Global module data map (moduledata for plugins, systemdata for system modules)
systemdata = {}
# filename = './log.txt'
logging.basicConfig(filename='./zcorelog.txt', level=logging.DEBUG)  # For debug logging
systemdata['syslog'] = 'on'  # turn 'on' for testing, otherwise 'off'
# ======================================================================================================================
# system modules - 'sys': These modules are designed to supplement the core functions. zcore only runs 1 sys module
#                         These modules can be imported\used with zcore plugins.
# zcore plugin modules - 'pm': These modules are specificially designed to run on zcore with sys_zcore enabled
#                               zcore can run multiple plugins
#                               zcore plugins can import sys_zcore functions
# custom modules - 'user': These are user defined modules that can be stand-alone from sys_zcore.
# ======================================================================================================================
# print function: mprint(string)
# ----------------------------------------------------------------------------------------------------------------------
# use this for printing to screen for zcore modules.
# mprint can be turned on/off by changing systemdata['moduleprint'] to True or False (see init process below)
def mprint(string):
    global systemdata
    if systemdata['moduleprint'] is True:
        print(f'[SYSTEM] * {string}')
    if systemdata['syslog'] == 'on':
        logging.debug(f'[SYSTEM] * {string}')
    return

# For remote mounting (required for all system modules)
# This allows for this module to be used on the system mount.
def system_call_():
    return True

def system_exit_():
    global systemdata
    mprint(f'System Exiting...')
    systemdata = {}
# ======================================================================================================================
# plug in functions (required for all system modules.)
# ======================================================================================================================
# zcore_plug_init(zcoreversion)
# system_init_(zcoreversion)
# This initiates the module when first loaded
def system_init_(zcoreversion):
    global systemdata
    # Main module data
    # Anything for configuration, put in here.
    # ##################################
    systemdata['moduleprint'] = True    # Set to False if you do not want module printing to screen/STDOUT (see mprint)
    # ##################################
    systemdata['access'] = True         # Set to False if you do not want to use the channel op/access features
    # ##################################
    systemdata['mname'] = 'zCore System Module I'  # Plugin title
    systemdata['mversion'] = '1.0'  # Core system version
    systemdata['mauthor'] = 'Neo Nemesis'  # author name
    systemdata['mtype'] = 'sys'  # 'sys' zcore system module, 'cpm' for custom module, 'ppm' for zcore module ?
    systemdata['mreqver'] = '0.1x'  # required zcore versions. (see version determination below)
    systemdata['serverlist'] = cnfread('zcore.cnf', 'zcore', 'serverlist').lower()
    systemdata['server'] = systemdata['serverlist'].split(',')
    systemdata['botmasters'] = cnfread('zcore.cnf', 'zcore', 'botmaster').lower()
    # Random use data
    systemdata['temp'] = ''
    # this prepares systemdata for channels and system admin/access.
    for x in range(len(systemdata['server'])):
        systemdata[systemdata['server'][x], 'nameschan'] = ''
        systemdata[systemdata['server'][x], 'channels'] = cnfread('zcore.cnf', systemdata['server'][x], 'channels').lower()
        systemdata[systemdata['server'][x], 'botname'] = cnfread('zcore.cnf', systemdata['server'][x], 'botname')
        # If channel(s) are specified, prepare userlist
        if systemdata[systemdata['server'][x], 'channels'] != '0':
            s_server = systemdata['server'][x]
            s_channel = systemdata[systemdata['server'][x], 'channels'].split(',')
            for y in range(len(s_channel)):
                s_chan = s_channel[y].replace('#', '')
                systemdata[s_server, s_chan] = {}
                systemdata[s_server, s_chan][s_chan] = 0
                continue
        systemdata[systemdata['server'][x], 'admins'] = cnfread('zcore.cnf', systemdata['server'][x], 'admin').lower()
        systemdata[systemdata['server'][x], 'access'] = cnfread('zcore.cnf', systemdata['server'][x], 'access').lower()
        systemdata[systemdata['server'][x], 'akick'] = cnfread('zcore.cnf', systemdata['server'][x], 'akick').lower()
        systemdata[systemdata['server'][x], 'changehost'] = b''
        continue
    # ------------------------------------------------------------------------------------------------------------------
    # version determination
    # Specify '*.*' for ' systemdata['mreqver'] = '*.*' ' bypasses the version check.
    # This method is experimental and is only suggested for advanced users.
    # Specify versions in a string, separated by ' , '
    # Example: systemdata['mreqver'] = '0.1x,0.1z' - this means the module works with version 0.1x and 0.1z of zcore.
    # ------------------------------------------------------------------------------------------------------------------
    # version requirement check
    systemdata['vdata'] = systemdata['mreqver'].split(',')
    if systemdata['mreqver'] != '*.*':
        # version does not match
        if zcoreversion not in systemdata['vdata']:
            mprint(f'{systemdata['mname']} * Version requirement does not match.')
            mprint(f'{systemdata['mname']} * Version {systemdata['mversion']} loaded but may produce errors.')
        # version check ok
        else:
            mprint(f'{systemdata['mname']} * Version {systemdata['mversion']} loaded successfully.')
    # version check bypass (experimental)
    if systemdata['mreqver'] == '*.*':
        mprint(f'{systemdata['mname']} * Version requirement byapssed, continuing...')
        mprint(f'{systemdata['mname']} * Version {systemdata['mversion']} loaded.')
        # return
    mprint(f'{systemdata['mname']} * Author: {systemdata['mauthor']}')

# ======================================================================================================================
# socket_stage(threadname, sock)
# Receives and assigns core socket data in systemdata
def socket_stage(threadname, sock):
    global systemdata
    systemdata[threadname, 'sock'] = sock
# ======================================================================================================================
# Event functions (used for modules and plugins)
# ======================================================================================================================
# PRIVMSG user/chan
async def exct_privmsg(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    userhost = gettok(udata[0], 1, b'!')
    dusername = username.decode()
    dusername = dusername.lower()
    # ------------------------------------------------------------------------------------------------------------------
    # PMs
    # :Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u PRIVMSG PyDuck :testing one two three'
    if udata[2].decode() == systemdata[threadname, 'botname']:
        # --------------------------------------------------------------------------------------------------------------
        # Administration functions
        # some functions are botmaster only, others are shared botmaster/admin.
        # --------------------------------------------------------------------------------------------------------------
        # /msg botname vcuser <add/rem> <username>
        # add and remove voice access users (botmaster and admin)
        if udata[3].lower() == b':vcuser':
            if istok(systemdata[threadname, 'admins'], dusername, ',') is True or istok(systemdata['botmasters'], dusername, ',') is True:
                if len(udata) > 5:
                    # --------------------------------------------------------------------------------------------------
                    # /msg botname vcuser add <username>
                    if udata[4].lower() == b'add':
                        # user is already listed as vcuser
                        if istok(bytes(systemdata[threadname, 'access'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is already listed in voice access for ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                        # user is already listed in another (botmaster list)
                        elif istok(bytes(systemdata['botmasters'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a botmaster.\r\n')
                            return
                            # user is already listed in another (access list)
                        elif istok(bytes(systemdata[threadname, 'admins'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a admin.\r\n')
                            return
                            # user is listed as akick
                        elif istok(bytes(systemdata[threadname, 'akick'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed for auto kick/ban.\r\n')
                            return
                        else:
                            vcname = udata[5].decode()
                            vcname = vcname.lower()
                            if systemdata[threadname, 'access'] == '0':
                                cnfwrite('zcore.cnf', threadname, 'access', vcname)
                                systemdata[threadname, 'access'] = vcname
                            else:
                                vcusers = systemdata[threadname, 'access'] + ',' + vcname
                                cnfwrite('zcore.cnf', threadname, 'access', vcusers)
                            mprint(f'{threadname} * Voice access added: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' added to the voice access list for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                    # --------------------------------------------------------------------------------------------------
                    # /msg botname vcuser rem <username>
                    if udata[4].lower() == b'rem':
                        # user does not exist in admin list
                        if istok(bytes(systemdata[threadname, 'access'], 'utf-8'), udata[5].lower(), b',') is False:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is not listed in voice access for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                        else:
                            remname = udata[5].decode()
                            remname = remname.lower()
                            if systemdata[threadname, 'access'] == remname:
                                cnfwrite('zcore.cnf', threadname, 'access', '0')
                                systemdata[threadname, 'access'] = '0'
                            else:
                                vcusers = deltok(systemdata[threadname, 'access'], remname, ',')
                                cnfwrite('zcore.cnf', threadname, 'access', vcusers)
                                systemdata[threadname, 'access'] = vcusers
                            mprint(f'{threadname} * Voice access removed: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' removed from the voice access list for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return

        # --------------------------------------------------------------------------------------------------------------
        # /msg botname admin <add/rem> <username>
        # add and remove admins (BOTMASTER ONLY)
        if udata[3].lower() == b':admin' and istok(systemdata['botmasters'], dusername, ',') is True:
            if len(udata) > 5:
                # /msg botname admin add <username>
                if udata[4].lower() == b'add':
                    # user already exists in admin list
                    if istok(bytes(systemdata[threadname, 'admins'], 'utf-8'), udata[5].lower(), b',') is True:
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is already listed as an admin for ' + bytes(threadname, 'utf-8') + b'\r\n')
                        return
                    # user is already listed in another (botmaster list)
                    elif istok(bytes(systemdata['botmasters'], 'utf-8'), udata[5].lower(), b',') is True:
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a botmaster.\r\n')
                        return
                    # user is already listed in another (access list)
                    elif istok(bytes(systemdata[threadname, 'access'], 'utf-8'), udata[5].lower(), b',') is True:
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a access user.\r\n')
                        return
                    # user is listed as akick
                    elif istok(bytes(systemdata[threadname, 'akick'], 'utf-8'), udata[5].lower(), b',') is True:
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed for auto kick/ban.\r\n')
                        return
                    else:
                        addname = udata[5].decode()
                        addname = addname.lower()
                        if systemdata[threadname, 'admins'] == '0':
                            cnfwrite('zcore.cnf', threadname, 'admin', addname)
                            systemdata[threadname, 'admins'] = addname
                        else:
                            admins = systemdata[threadname, 'admins'] + ',' + addname
                            cnfwrite('zcore.cnf', threadname, 'admin', admins)
                        mprint(f'{threadname} * Admin added: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' added to the admin list for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                        return
                # /msg botname admin rem <username>
                if udata[4].lower() == b'rem':
                    # user does not exist in admin list
                    if istok(bytes(systemdata[threadname, 'admins'], 'utf-8'), udata[5].lower(), b',') is False:
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is not listed as an admin for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                        return
                    else:
                        remname = udata[5].decode()
                        remname = remname.lower()
                        if systemdata[threadname, 'admins'] == remname:
                            cnfwrite('zcore.cnf', threadname, 'admin', '0')
                            systemdata[threadname, 'admins'] = '0'
                        else:
                            admins = deltok(systemdata[threadname, 'admins'], remname, ',')
                            cnfwrite('zcore.cnf', threadname, 'admin', admins)
                            systemdata[threadname, 'admins'] = admins
                        mprint(f'{threadname} * Admin removed: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' removed from the admin list for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                        return
        # --------------------------------------------------------------------------------------------------------------
        # /msg botname akick <add/rem> <username>
        # add and remove akicks (botmaster and admin)
        if udata[3].lower() == b':akick':
            if istok(systemdata['botmasters'], dusername, ',') is True or istok(systemdata[threadname, 'admins'], dusername, ',') is True:
                if len(udata) > 5:
                    # /msg botname akick add <username>
                    if udata[4].lower() == b'add':
                        # user already exists in akick list
                        if istok(bytes(systemdata[threadname, 'akick'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is already listed for auto kick/ban for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                        # user is already listed in another (botmaster list)
                        elif istok(bytes(systemdata['botmasters'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a botmaster.\r\n')
                            return
                        # user is already listed in another (access list)
                        elif istok(bytes(systemdata[threadname, 'access'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a access user.\r\n')
                            return
                        # user is listed as admin
                        elif istok(bytes(systemdata[threadname, 'admins'], 'utf-8'), udata[5].lower(), b',') is True:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is currently listed as a admin.\r\n')
                            return
                        else:
                            addname = udata[5].decode()
                            addname = addname.lower()
                            if systemdata[threadname, 'akick'] == '0':
                                cnfwrite('zcore.cnf', threadname, 'akick', addname)
                                systemdata[threadname, 'akick'] = addname
                            else:
                                akicks = systemdata[threadname, 'akick'] + ',' + addname
                                cnfwrite('zcore.cnf', threadname, 'akick', akicks)
                            mprint(f'{threadname} * Akick added: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' added to the auto kick/ban for: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                    # /msg botname akick rem <username>
                    if udata[4].lower() == b'rem':
                        # user does not exist in akick list
                        if istok(bytes(systemdata[threadname, 'akick'], 'utf-8'), udata[5].lower(), b',') is False:
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :Invalid request: ' + udata[5] + b' is not listed for auto kick/ban on: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return
                        else:
                            remname = udata[5].decode()
                            remname = remname.lower()
                            if systemdata[threadname, 'akick'] == remname:
                                cnfwrite('zcore.cnf', threadname, 'akick', '0')
                                systemdata[threadname, 'akick'] = '0'
                            else:
                                akicks = deltok(systemdata[threadname, 'akick'], remname, ',')
                                cnfwrite('zcore.cnf', threadname, 'akick', akicks)
                                systemdata[threadname, 'akick'] = akicks
                            mprint(f'{threadname} * Akick removed: {udata[5].decode()} by {username.decode()} {userhost.decode()}')
                            systemdata[threadname, 'sock'].send(b'NOTICE ' + username + b' :' + udata[5] + b' removed from auto kick/ban on: ' + bytes(threadname, 'utf-8') + b'\r\n')
                            return

        # --------------------------------------------------------------------------------------------------------------
        # print
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ' + udata[1] + b' ' + udata[2] + b' ', udata[1] + b' ')}')
    # ------------------------------------------------------------------------------------------------------------------
    # Channel Messages
    else:
        # print
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ', b'')}')
        # --------------------------------------------------------------------------------------------------------------
        # !slap - originally used for testing is_on_chan function
        if udata[3].lower() == b':!slap' and len(udata) > 4:
            if is_on_chan(threadname, udata[2], udata[4]) is True:
                systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :\x01ACTION slaps ' + udata[4] + b' around a bit with a large trout\x01\r\n')
            else:
                systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\x01\r\n')
            return
        # --------------------------------------------------------------------------------------------------------------
        # !voice self auth and !devoice self auth for access users
        if istok(systemdata[threadname, 'access'], dusername, ',') is True:
            # ----------------------------------------------------------------------------------------------------------
            # !voice (self auth for access users)
            if udata[3].lower() == b':!voice' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                if len(udata) == 4:
                    if is_vc(threadname, udata[2], username) is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You already have voice\r\n')
                        return
                    mprint(f'{threadname} * !voice command access * {username.lower()} {userhost.lower()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +v ' + username + b'\r\n')
                    return
                return
            # ----------------------------------------------------------------------------------------------------------
            # !devoice (self auth for access users)
            if udata[3].lower() == b':!devoice' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                if len(udata) == 4:
                    if is_vc(threadname, udata[2], username) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You do not have voice\r\n')
                        return
                    mprint(f'{threadname} * !devoice command access * {username.lower()} {userhost.lower()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -v ' + username + b'\r\n')
                    return
                return
        # --------------------------------------------------------------------------------------------------------------
        # Botmaster and admin commands
        if istok(systemdata['botmasters'], dusername, ',') is True or istok(systemdata[threadname, 'admins'], dusername, ',') is True:
            # ----------------------------------------------------------------------------------------------------------
            # !op and !op <username>
            if udata[3].lower() == b':!op' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                # !op (self auth)
                if len(udata) == 4:
                    if is_op(threadname, udata[2], username) is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You already have op\r\n')
                        return
                    mprint(f'{threadname} * !op command self authorized * {username.decode()} {userhost.decode()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +o ' + username + b'\r\n')
                    return
                if len(udata) > 4:
                    dname = udata[4].decode()
                    if dname.lower() == systemdata[threadname, 'botname'].lower():
                        return
                    if is_on_chan(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                        return
                    if is_op(threadname, udata[2], udata[4]) is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :' + udata[4] + b' already has op\r\n')
                        return
                    opname = udata[4].decode()
                    opname = opname.lower()
                    # !op <admin/botmaster> (access auth)
                    if istok(systemdata['botmasters'], opname, ',') is True or istok(systemdata[threadname, 'admins'], opname, ',') is True:
                        mprint(f'{threadname} * !op access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +o ' + udata[4] + b'\r\n')
                        return
                    # !op <username> (guest auth)
                    else:
                        mprint(f'{threadname} * !op command temporary guest: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +o ' + udata[4] + b'\r\n')
                        return
                return
            # ----------------------------------------------------------------------------------------------------------
            # !deop and !deop <username>
            if udata[3].lower() == b':!deop' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                # !deop (self auth)
                if len(udata) == 4:
                    if is_op(threadname, udata[2], username) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You do not have op\r\n')
                        return
                    mprint(f'{threadname} * !deop command self authorized * {username.decode()} {userhost.decode()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -o ' + username + b'\r\n')
                    return
                if len(udata) > 4:
                    dname = udata[4].decode()
                    if dname.lower() == systemdata[threadname, 'botname'].lower():
                        return
                    if is_on_chan(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                        return
                    if is_op(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :' + udata[4] + b' does not have op\r\n')
                        return
                    opname = udata[4].decode()
                    opname = opname.lower()
                    # !deop <admin/botmaster> (access auth)
                    if istok(systemdata['botmasters'], opname, ',') is True or istok(systemdata[threadname, 'admins'], opname, ',') is True:
                        mprint(f'{threadname} * !deop access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -o ' + udata[4] + b'\r\n')
                        return
                    # !deop <username> (guest auth)
                    else:
                        mprint(f'{threadname} * !deop command temporary guest: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -o ' + udata[4] + b'\r\n')
                        return
                return
            # ----------------------------------------------------------------------------------------------------------
            # !voice and !voice <username>
            if udata[3].lower() == b':!voice' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                # !voice (self auth)
                if len(udata) == 4:
                    if is_vc(threadname, udata[2], username) is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You already have voice\r\n')
                        return
                    mprint(f'{threadname} * !voice command self authorized * {username.decode()} {userhost.decode()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +v ' + username + b'\r\n')
                    return
                if len(udata) > 4:
                    dname = udata[4].decode()
                    if dname.lower() == systemdata[threadname, 'botname'].lower():
                        return
                    if is_on_chan(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                        return
                    if is_op(threadname, udata[2], udata[4]) is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :' + udata[4] + b' already has voice\r\n')
                        return
                    opname = udata[4].decode()
                    opname = opname.lower()
                    # !voice <admin/botmaster> (access auth)
                    if istok(systemdata['botmasters'], opname, ',') is True or istok(systemdata[threadname, 'admins'], opname, ',') is True:
                        mprint(f'{threadname} * !voice access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +v ' + udata[4] + b'\r\n')
                        return
                    # !voice <username> (guest auth)
                    else:
                        mprint(f'{threadname} * !voice command temporary guest: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +v ' + udata[4] + b'\r\n')
                        return
                return
            # ----------------------------------------------------------------------------------------------------------
            # !devoice and !devoice <username>
            if udata[3].lower() == b':!devoice' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
                # !deop (self auth)
                if len(udata) == 4:
                    if is_vc(threadname, udata[2], username) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :You do not have voice\r\n')
                        return
                    mprint(f'{threadname} * !devoice command self authorized * {username.decode()} {userhost.decode()}')
                    systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -v ' + username + b'\r\n')
                    return
                if len(udata) > 4:
                    dname = udata[4].decode()
                    if dname.lower() == systemdata[threadname, 'botname'].lower():
                        return
                    if is_on_chan(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                        return
                    if is_vc(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :' + udata[4] + b' does not have voice\r\n')
                        return
                    opname = udata[4].decode()
                    opname = opname.lower()
                    # !devoice <admin/botmaster> (access auth)
                    if istok(systemdata['botmasters'], opname, ',') is True or istok(systemdata[threadname, 'admins'], opname, ',') is True:
                        mprint(f'{threadname} * !devoice access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -v ' + udata[4] + b'\r\n')
                        return
                    # !devoice <username> (guest auth)
                    else:
                        mprint(f'{threadname} * !devoice command temporary guest: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -v ' + udata[4] + b'\r\n')
                        return
                return
            # ----------------------------------------------------------------------------------------------------------
            # !kick <username> (Kick user)
            if udata[3].lower() == b':!kick' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True and len(udata) > 4:
                if udata[4].lower() == username.lower():
                    mprint(f'{threadname} * !kick authorized: {username.decode()} kicked their own ass...')
                    systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + username + b' :Stop hitting yourself\r\n')
                    return
                if udata[4].lower() == bytes(systemdata[threadname, 'botname'].lower(), 'utf-8'):
                    systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :Don't kick the bot...\r\n")
                    return
                if is_on_chan(threadname, udata[2], udata[4]) is False:
                    systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                    return
                kickname = udata[4].decode()
                kickname = kickname.lower()
                if istok(systemdata['botmasters'], kickname, ',') is True:
                    if istok(systemdata['botmasters'], dusername, ',') is True:
                        mprint(f'{threadname} * !kick botmaster authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + udata[4] + b' :Requested by ' + username + b'\r\n')
                        return
                    systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :Access denied.\r\n')
                    return
                else:
                    # HERE
                    mprint(f'{threadname} * !kick access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                    systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + udata[4] + b' :Requested by ' + username + b'\r\n')
                    return
            # ----------------------------------------------------------------------------------------------------------
            # !ban <username> or !kb <username> (Kick and ban)
            if udata[3].lower() == b':!ban' or udata[3].lower() == b':!kb':
                if is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True and len(udata) > 4:
                    if udata[4].lower() == username.lower():
                        mprint(f'{threadname} * !ban authorized: {username.decode()} banned themselves...')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +b ' + username + b'\r\n')
                        systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + username + b' :Well, at that point, ' + username + b' f@#$%ed up.\r\n')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -b ' + username + b'\r\n')
                        return
                    if udata[4].lower() == bytes(systemdata[threadname, 'botname'].lower(), 'utf-8'):
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :Don't ban the bot...\r\n")
                        return
                    if is_on_chan(threadname, udata[2], udata[4]) is False:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b" :\x01ACTION doesn't see " + udata[4] + b'\r\n')
                        return
                    banname = udata[4].decode()
                    banname = banname.lower()
                    if istok(systemdata['botmasters'], banname, ',') is True:
                        systemdata[threadname, 'sock'].send(b'PRIVMSG ' + udata[2] + b' :Access denied.\r\n')
                        return
                    else:
                        # HERE
                        mprint(f'{threadname} * !ban access authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                        systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +b ' + udata[4] + b'\r\n')
                        systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + udata[4] + b' :Requested by ' + username + b'\r\n')
                        return
            # ----------------------------------------------------------------------------------------------------------
            # !unban <username>
            if udata[3].lower() == b':!unban' and is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True and len(udata) > 4:
                mprint(f'{threadname} * !unban authorized: {udata[4].decode()} by {username.decode()} {userhost.decode()}')
                systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' -b ' + udata[4] + b'!*@*\r\n')
                return
    return

# ======================================================================================================================
# PRIVMSG chan/user :\x01ACTION
async def exct_action(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    # main module print for PRIVMSG :\x01ACTION
    if udata[2].decode() == systemdata[threadname, 'botname']:
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ' + udata[1] + b' ' + udata[2] + b' ', udata[1] + b' ')}')
    else:
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ', b'')}')
    return
# ======================================================================================================================
# NOTICE chan/user
# b':Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u NOTICE zcore :test'
async def exct_notice(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    # check for username!@host.name.net
    try:
        userhost = gettok(udata[0], 1, b'!')
    # server notice
    except IndexError:
        userhost = '0'
    if udata[3].lower() == b':***' and userhost == '0':
        mprint(f'{recv}')
        return
    # main module print for NOTICE
    if udata[2].decode() == systemdata[threadname, 'botname']:
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ' + udata[1] + b' ' + udata[2] + b' ', udata[1] + b' ')}')
    else:
        mprint(f'{threadname} ---> {username.decode()} {recv.replace(udata[0] + b' ', b'')}')
    return
# ======================================================================================================================
# JOIN
# b':Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u JOIN :#testduck'
async def exct_join(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    userhost = gettok(udata[0], 1, b'!')
    dusername = username.decode()
    dusername = dusername.lower()
    mprint(f'{threadname} * JOIN {udata[2].decode()} * {username.decode()} {userhost.decode()}')
    # this is for when a user QUIT Changing Host (to immediately rejoin)
    if username.lower() == systemdata[threadname, 'changehost'].lower():
        systemdata[threadname, 'changehost'] = b''
        return
    # bot is joining the channel
    if username.decode() == systemdata[threadname, 'botname']:
        return
    # add user to the user list
    await ul_edit(threadname, 'add', udata[2], username)
    # ------------------------------------------------------------------------------------------------------------------
    # Auto Op
    if istok(systemdata['botmasters'], dusername, ',') is True or istok(systemdata[threadname, 'admins'], dusername, ',') is True:
        if is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
            if is_op(threadname, udata[2], username) is False:
                systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +o ' + username + b'\r\n')
                return
    # ------------------------------------------------------------------------------------------------------------------
    # Auto Voice
    if istok(systemdata[threadname, 'access'], dusername, ',') is True:
        if is_vc(threadname, udata[2], username) is False:
            systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +v ' + username + b'\r\n')
            return
    # ------------------------------------------------------------------------------------------------------------------
    # Auto Kick (ban+kick on join)
    if istok(systemdata[threadname, 'akick'], dusername, ',') is True:
        if is_op(threadname, udata[2], bytes(systemdata[threadname, 'botname'], 'utf-8')) is True:
            systemdata[threadname, 'sock'].send(b'MODE ' + udata[2] + b' +b ' + username + b'\r\n')
            systemdata[threadname, 'sock'].send(b'KICK ' + udata[2] + b' ' + username + b' :AUTO KICK/BAN\r\n')
            return
    return
# ======================================================================================================================
# PART
# b':Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u PART #testduck'
async def exct_part(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    userhost = gettok(udata[0], 1, b'!')
    mprint(f'{threadname} * PART {udata[2].decode()} * {username.decode()} {userhost.decode()}')
    if username.decode() == systemdata[threadname, 'botname']:
        return
    await ul_edit(threadname, 'rem', udata[2], username)
    return
# ======================================================================================================================
# KICK
# b':Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u KICK #testduck zcore :testing 1 2 3'
async def exct_kick(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    kickmsg = recv.replace(udata[0] + b' ' + udata[1] + b' ' + udata[2] + b' ' + udata[3], b'')
    kusername = udata[3].lower()
    mprint(f'{threadname} * KICK {udata[2].decode()} * {username.decode()} ---> {udata[3].decode()} ({kickmsg})')
    if kusername.decode() == systemdata[threadname, 'botname'].lower():
        time.sleep(1.5)
        systemdata[threadname, 'sock'].send(b'JOIN ' + udata[2] + b'\r\n')
    else:
        await ul_edit(threadname, 'rem', udata[2], udata[3])
    return
# ======================================================================================================================
# MODE
# User mode +v +o etc: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +v zcore'
# Channel mode +i, +s etc: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +i '
# Channel ban +b: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +b *!*@Test'
async def exct_mode(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    if len(udata) > 4:
        mprint(f'{threadname} * MODE {udata[2].decode()} * {username.decode()} ---> {udata[3].decode()} {udata[4].decode()}')
    else:
        mprint(f'{threadname} * MODE {udata[2].decode()} * {username.decode()} ---> {udata[3].decode()}')
    if len(udata) > 4 and udata[3] != b'+b':
        mchan = udata[2].decode()
        mchan = mchan.replace('#', '')
        mchan = mchan.lower()
        systemdata[threadname, mchan] = {}
        systemdata[threadname, mchan][mchan] = 0
        systemdata[threadname, 'sock'].send(b'NAMES ' + udata[2] + b'\r\n')
    return
# ======================================================================================================================
# TOPIC
# b':Neo_Nemesis!~TheOne@hostmask.net TOPIC #TestWookie :test'
# async def exct_topic(threadname, recv):
async def exct_topic(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    mprint(f'{threadname} * {username.decode()} ---> {recv.replace(udata[0] + b' ', b'')}')
    return
# ======================================================================================================================
# NICK
# b':Testing!Mibbit@hostmask.net NICK :Test123'
# Needs more work, not finished!
async def exct_nick(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    newuser = udata[2].replace(b':', b'')
    mprint(f'{threadname} * NICK {username.decode()} ---> {udata[2].replace(b':', b'')}')
    n_chan = systemdata[threadname, 'channels'].split(',')
    # Either do this or spam /NAMES on every channel that user is in?
    for x in range(len(n_chan)):
        nchan = n_chan[x].replace('#', '')
        nchan = nchan.lower()
        for y in range(len(systemdata[threadname, nchan])):
            if y == 0:
                continue
            # 'username'
            if istok(systemdata[threadname, nchan][y].lower(), username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), newuser)
                continue
            # '~username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'~' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'~' + newuser)
                continue
            # '&username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'&' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'&' + newuser)
                continue
            # '!username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'!' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'!' + newuser)
                continue
            # '@username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'@' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'@' + newuser)
                continue
            # '%username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'%' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'%' + newuser)
                continue
            # '+username'
            elif istok(systemdata[threadname, nchan][y].lower(), b'+' + username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(n_chan[x], 'utf-8'), username)
                await ul_edit(threadname, 'add', bytes(n_chan[x], 'utf-8'), b'+' + newuser)
                continue
            continue
    return
# ======================================================================================================================
# QUIT
# b':Test123!Mibbit@hostmask.net QUIT :Client Quit'
# #######################
# Added a check for QUIT :Changing host
# for userlists (on some servers?)
# Set a variable with username to be picked up by exct_join
# Doing this will ignore the QUIT and second JOIN from the user changing hosts
# ########################
async def exct_quit(threadname, recv):
    global systemdata
    udata = recv.split(b' ')
    username = gettok(udata[0], 0, b'!').replace(b':', b'')
    mprint(f'{threadname} * {username.decode()} ---> {recv.replace(udata[0] + b' ', b'')}')
    # This is for QUIT Changing Host
    if udata[2].lower() == b':changing' and udata[3].lower() == b'host':
        systemdata[threadname, 'changehost'] = username
        return
    q_chan = systemdata[threadname, 'channels'].split(',')
    for x in range(len(q_chan)):
        qchan = q_chan[x].replace('#', '')
        qchan = qchan.lower()
        for y in range(len(systemdata[threadname, qchan])):
            if y == 0:
                continue
            if istok(ul_cleaner(systemdata[threadname, qchan][y]).lower(), username.lower(), b' ') is True:
                await ul_edit(threadname, 'rem', bytes(q_chan[x], 'utf-8'), username)
                continue
        continue
    return
# ======================================================================================================================
# RAW
async def exct_raw(threadname, raw, recv):
    global systemdata
    rdata = recv.split(b' ')
    # 353 /NAMES reply
    # :servername 353 botname @ #channel :username1, @username2, username3, &username4, etc
    if raw == b'353' and len(rdata) > 5:
        n_chan = rdata[4].decode()
        n_chan = n_chan.lower()
        systemdata[threadname, 'nameschan'] = n_chan
        ul_build(threadname, n_chan, recv)
        return
    # 366 /NAMES end
    # :servername 366 botname #channel :End of /NAMES list.
    if raw == b'366' and len(rdata) > 4:
        systemdata[threadname, 'nameschan'] = ''
        mprint(f'{threadname} * End of /NAMES {rdata[3].decode()}.')
        return

    mprint(f'{threadname} ---> {recv}')
    return
# ======================================================================================================================
# exct_chk
async def exct_chk(threadname, recv):
    global systemdata
    # ------------------------------------------------------------------------------------------------------------------
    # check for user list errors
    str_err_chk = recv
    if str_err_chk.find(b':') == -1 and systemdata[threadname, 'nameschan'] != '':
        ul_err_fix(threadname, recv)
        return
# ======================================================================================================================
# System Userlist Functions
# These are functions used for userlist data handling.
# ----------------------------------------------------------------------------------------------------------------------
# Create a user list
def ul_build(threadname, chan, namesdata):
    global systemdata
    # systemdata[s_server, s_chan] = {}
    # systemdata[threadname, channel][x] = block x
    # len(systemdata[threadname, channel]) = total amount of lists
    ulchan = chan.lower()
    ulchan = ulchan.replace('#', '')
    ulnum = int(systemdata[threadname, ulchan][ulchan]) + 1
    ultmp = b''
    if numtok(namesdata, b':') == 3:
        ultmp = gettok(namesdata, 2, b':')
    if numtok(namesdata, b':') < 3:
        ultmp = gettok(namesdata, 1, b':')
    systemdata[threadname, ulchan][ulchan] = ulnum
    systemdata[threadname, ulchan][ulnum] = ultmp
    mprint(f'{threadname} * /NAMES #{ulchan}: [{ulnum}] {ultmp}')
    return
# ======================================================================================================================
# fixes broken character strings during list creation
def ul_err_fix(threadname, recvdata):
    global systemdata
    errchan = systemdata[threadname, 'nameschan']
    errchan = errchan.replace('#', '')
    errnum = int(systemdata[threadname, errchan][errchan])
    str_err = systemdata[threadname, errchan][errnum]
    str_fix = str_err + recvdata
    systemdata[threadname, errchan][errnum] = str_fix
    mprint(f'{threadname} * USER LIST ERROR FOUND.')
    mprint(f'{threadname} * FIX - /NAMES #{errchan}: [{errnum}] {systemdata[threadname, errchan][errnum]}')
    return 1
# ======================================================================================================================
# Takes a string of usernames and removes channel mode characters.
def ul_cleaner(ultext):
    cleaner = ultext.replace(b'@', b'')
    cleaner = cleaner.replace(b'~', b'')
    cleaner = cleaner.replace(b'!', b'')
    cleaner = cleaner.replace(b'%', b'')
    cleaner = cleaner.replace(b'+', b'')
    cleaner = cleaner.replace(b'&', b'')
    cleaner = cleaner.replace(b', ', b' ')
    cleaner = cleaner.replace(b',', b' ')
    # mprint(f'* CLEANER TEST: {cleaner}')
    return cleaner
# ======================================================================================================================
# add or remove a nickname from user list
async def ul_edit(threadname, args, chan, user):
    global systemdata
    edchan = chan.decode()
    edchan = edchan.replace('#', '')
    edchan = edchan.replace(':', '')
    edchan = edchan.lower()
    # ------------------------------------------------------------------------------------------------------------------
    # ul_edit(threadname, 'add', b'#channel', b'username')
    # add user to user list
    if args.lower() == 'add':
        ul_tnum = int(systemdata[threadname, edchan][edchan])
        ul_user = systemdata[threadname, edchan][ul_tnum].split(b' ')
        if len(ul_user) >= 40:
            ul_tnum += 1
            systemdata[threadname, edchan][ul_tnum] = user
        else:
            systemdata[threadname, edchan][ul_tnum] = systemdata[threadname, edchan][ul_tnum] + b' ' + user
        ul_list(threadname, chan)
        return
    # ------------------------------------------------------------------------------------------------------------------
    # ul_edit(threadname, 'rem', b'#channel, b'username')
    # remove user from channel user list (PART, KICK)
    if args.lower() == 'rem':
        for x in range(len(systemdata[threadname, edchan])):
            if x == 0:
                continue
            ul = systemdata[threadname, edchan][x]
            ul = ul_cleaner(ul)
            if iistok(ul.lower(), user.lower(), b' ') is True:
                ul_str = systemdata[threadname, edchan][x].split(b' ')
                ul_n = b''
                for y in range(len(ul_str)):
                    if ul_cleaner(ul_str[y]).lower() == user.lower():
                        continue
                    else:
                        if ul_n == b'':
                            ul_n = ul_str[y]
                            continue
                        else:
                            ul_n = ul_n + b' ' + ul_str[y]
                            continue
                systemdata[threadname, edchan][x] = ul_n
                ul_list(threadname, chan)
                return
            continue
        return
# ======================================================================================================================
# ul_remuser(threadname, chan, user)
# only for ul_edit()
def ul_remuser(threadname, chan, user):
    global systemdata
    edchan = chan.decode()
    edchan = edchan.replace('#', '')
    edchan = edchan.replace(':', '')
    edchan = edchan.lower()
    for x in range(len(systemdata[threadname, edchan])):
        if x == 0:
            continue
        ul = systemdata[threadname, edchan][x]
        ul = ul_cleaner(ul)
        if iistok(ul.lower(), user.lower(), b' ') is True:
            ul_str = systemdata[threadname, edchan][x].split(b' ')
            ul_n = b''
            for y in range(len(ul_str)):
                if ul_cleaner(ul_str[y]).lower() == user.lower():
                    continue
                else:
                    if ul_n == b'':
                        ul_n = ul_str[y]
                        continue
                    else:
                        ul_n = ul_n + b' ' + ul_str[y]
                        continue
            systemdata[threadname, edchan][x] = ul_n
            # mprint(f'UL_STR: {ul_n} USER: {user}')
            ul_list(threadname, chan)
            return
        continue
    return
# ======================================================================================================================
# lists userlist for specified channel to screen (testing purposes)
def ul_list(threadname, chan):
    global systemdata
    lchan = chan.lower()
    lchan = lchan.decode()
    lchan = lchan.replace('#', '')
    lchan = lchan.replace(':', '')
    if systemdata[threadname, lchan][lchan] == 0:
        mprint(f'{threadname} * {chan} Userlist empty.')
        return
    else:
        for x in range(len(systemdata[threadname, lchan])):
            if x == 0:
                continue
            mprint(f'{threadname} * {chan} Userlist [{x}]: {systemdata[threadname, lchan][x]}')
            continue
    return

# ======================================================================================================================
# System Utility Functions
# These are functions that can be used for bridging the system to a zcore module.

# is_on_chan(threadname, chan, user) -----------------------------------------------------------------------------------
# determines if user is on channel
def is_on_chan(threadname, chan, user):
    global systemdata
    onchan = chan.decode()
    onchan = onchan.lower()
    onchan = onchan.replace('#', '')
    for x in range(len(systemdata[threadname, onchan])):
        if x == 0:
            continue
        else:
            ul_l = ul_cleaner(systemdata[threadname, onchan][x])
            if istok(ul_l.lower(), user.lower(), b' ') is True:
                return True
            else:
                continue
    return False

# is_op(threadname, chan, user) ----------------------------------------------------------------------------------------
# determines if user has operator status on channel
def is_op(threadname, chan, user):
    global systemdata
    opchan = chan.decode()
    opchan = opchan.lower()
    opchan = opchan.replace('#', '')
    opchan = opchan.replace(':', '')
    for x in range(len(systemdata[threadname, opchan])):
        if x == 0:
            continue
        else:
            if istok(systemdata[threadname, opchan][x].lower(), b'%' + user.lower(), b' ') is True:
                return True
            elif istok(systemdata[threadname, opchan][x].lower(), b'@' + user.lower(), b' ') is True:
                return True
            elif istok(systemdata[threadname, opchan][x].lower(), b'&' + user.lower(), b' ') is True:
                return True
            elif istok(systemdata[threadname, opchan][x].lower(), b'!' + user.lower(), b' ') is True:
                return True
            elif istok(systemdata[threadname, opchan][x].lower(), b'~' + user.lower(), b' ') is True:
                return True
            else:
                continue
    return False

# is_vc(threadname, chan, user) ----------------------------------------------------------------------------------------
# determines is user has voice +v on channel
def is_vc(threadname, chan, user):
    global systemdata
    vchan = chan.decode()
    vchan = vchan.lower()
    vchan = vchan.replace('#', '')
    for x in range(len(systemdata[threadname, vchan])):
        if x == 0:
            continue
        else:
            if istok(systemdata[threadname, vchan][x].lower(), b'+' + user.lower(), b' ') is True:
                return True
            else:
                continue
    return False

# is_botmaster(user) ---------------------------------------------------------------------------------------------------
# determines if user is listed in the zcore bot master list.
def is_botmaster(user):
    global systemdata
    if user.lower() in systemdata['botmasters']:
        return True
    else:
        return False

# is_chan(threadname, chan) --------------------------------------------------------------------------------------------
# determines if specified channel is in threadname channel list
def is_chan(threadname, chan):
    global systemdata
    if chan.lower() in systemdata[threadname, 'channels']:
        return True
    else:
        return False

# is_admin(threadname, user) -------------------------------------------------------------------------------------------
# determines if specified user is an admin on threadname
def is_admin(threadname, user):
    global systemdata
    if istok(systemdata['botmasters'], user.lower(), ',') is True:
        return True
    if istok(systemdata[threadname, 'admins'], user.lower(), ',') is True:
        return True
    if user.lower() + ',' in systemdata['botmasters'].lower() or user.lower() == systemdata[threadname, 'admins'].lower():
        return True
    else:
        return False

# is_access(threadname, user) ------------------------------------------------------------------------------------------
def is_access(threadname, user):
    global systemdata
    if user.lower() in systemdata[threadname, 'access']:
        return True
    else:
        return False

# ======================================================================================================================
# User Defined Scripting and general use functions (import sys_zcore as pc)

# percent(per, value) --------------------------------------------------------------------------------------------------
# Returns a floating number percentage of a whole number value. percent(P%, X)
# used in trivia-master hint randomizer
# percent(50, 200) returns 100.0     50% of 200
# percent(50, 5) returns 2.5         50% of 5
# percent(30, 3) returns 0.9         30% of 3
def percent(per, value):
    math = per * value / 100
    # print(f'Percent: {math}')
    return math

# rand(X, y) -----------------------------------------------------------------------------------------------------------
def rand(x, y):
    return random.randint(x, y)

# bot_sleep(value) -----------------------------------------------------------------------------------------------------
# uses time.sleep(value)
def bot_sleep(value):
    time.sleep(value)
    return

# cputime() ------------------------------------------------------------------------------------------------------------
# returns time.time()
def cputime():
    return time.time()

# **[ Date and Time Functions ]=========================================================================================
# Current Date ---------------------------------------------------------------------------------------------------------
def cdate():
    to_day = date.today()
    return to_day.strftime("%B %d, %Y")

# Current Time ---------------------------------------------------------------------------------------------------------
def ctime():
    now = datetime.now()
    return now.strftime("%H:%M:%S")

# Current hour of the day ----------------------------------------------------------------------------------------------
def chour():
    now = datetime.now()
    tok = now.strftime("%H:%M:%S").split(':')
    return tok[0]

# Current Day of the year ----------------------------------------------------------------------------------------------
def cday():
    return gettok(str(date.today()), 2, '-')

# Current Week of the year ---------------------------------------------------------------------------------------------
def cweek():
    return str(date.today().isocalendar()[1])

# Current Month of the year --------------------------------------------------------------------------------------------
def cmonth():
    return gettok(str(date.today()), 1, '-')

# Current year
def cyear():
    return gettok(str(date.today()), 0, '-')

# 1 hour in seconds (3600) ---------------------------------------------------------------------------------------------
def hour1():
    return 3600

# 24 hours in seconds (86400) ------------------------------------------------------------------------------------------
def hour24():
    return 86400

# **[ File Handling Functions ]=========================================================================================
# Returns True if file exists, otherwise False -------------------------------------------------------------------------
def isfile(filename):
    return os.path.isfile(filename)

# Removes single file in script directory ------------------------------------------------------------------------------
# Designed for plugin use in editing text files
def remfile(filename):
    os.remove(filename)
    return

# Renames a single file ------------------------------------------------------------------------------------------------
def renamefile(file, newfile):
    os.rename(file, newfile)
    return

# deletes specified key from section in cnf file. ----------------------------------------------------------------------
def cnfdelete(file, section, key):
    config = configparser.ConfigParser()
    config.read(file)
    if config.has_option(section, key):
        config.remove_option(section, key)
        with open(file, 'w') as conf:
            config.write(conf)
            return True
    return False

# returns true if specified cnf file list and key entry exists. --------------------------------------------------------
def cnfexists(file, section, key):
    config = configparser.ConfigParser()
    config.read(file)
    if config.has_option(section, key):
        return True
    else:
        return False

# read from cnf file lists ---------------------------------------------------------------------------------------------
def cnfread(file, section, key):
    config_object = ConfigParser()
    config_object.read(file)
    info = config_object[section]
    return format(info[key])

# write to cnf file lists ----------------------------------------------------------------------------------------------
def cnfwrite(file, section, key, data):
    try:
        config_object = ConfigParser()
        config_object.read(file)
        info = config_object[section]
        info[key] = data
        with open(file, 'w') as conf:
            config_object.write(conf)
    except KeyError:
        config = configparser.ConfigParser()

        config[section] = {key: data}
        with open(file, 'a') as configfile:
            config.write(configfile)
    return
# write to txt files ---------------------------------------------------------------------------------------------------
def txtwrite(filename, text):
    print(f'{filename}')
    file = open(filename, 'a')
    file.write(str(text) + '\n')
    file.close()
    return
# **[ Token List Functions ]==========================================================================================
# Token Lists are a sequence of data having a collective meaning. Each token is a individual value of data
# Token Lists are a collection of related data.

# istok(string, token, char) -------------------------------------------------------------------------------------------
# used by is_on_chan and is_op functions
def istok(string, token, char):
    if char + token + char in string or char + token in string or token + char in string or string == token:
        return True
    else:
        return False

# Returns True if specified token exists in token string, otherwise false. ---------------------------------------------
# iistok('A,B,C,D,E', 'D', ',') - Returns True
# iistok('A,B,C,D,E', 'F', ',') - Returns False
def iistok(string, token, char):
    dat = string.split(char)
    for x in range(len(dat)):
        if dat[x] == token:
            return True
        else:
            x += 1
            continue
    return False

# Get specified token from token string --------------------------------------------------------------------------------
# gettok('A,B,C,D', '2', ',') - Returns "C"
def gettok(string, x, char):
    data = string.split(char)
    return data[x]

# Number of total tokens in string -------------------------------------------------------------------------------------
# numtok('A,B,C,D,E', ',') - Returns 5
def numtok(string, char):
    dat = string.split(char)
    return len(dat)

# Delete a specified token from token string ---------------------------------------------------------------------------
# deltok('Z,A,B,Z,C,D,E', 'Z', ',') - Returns 'A,B,C,D,E'
def deltok(string, token, char):
    data = string.split(char)
    newstring = ''
    for x in range(len(data)):
        if data[x] == token:
            continue
        if data[x] != token:
            if newstring == '':
                newstring = data[x]
                continue
            if newstring != '':
                newstring = newstring + char + data[x]
                continue
    return newstring

# Replaces a token in a token string -----------------------------------------------------------------------------------
# reptok('A,B,C,D', '2', ',', 'X') - Returns "A,B,X,D"
def reptok(string, x, char, tok):
    data = string.split(char)
    newstring = ''
    for z in range(len(data)):
        if z == x:
            if newstring == '':
                newstring = tok
                z += 1
                continue
            if newstring != '':
                newstring = newstring + char + tok
                z += 1
                continue
        if z != x:
            if newstring == '':
                newstring = data[z]
                z += 1
                continue
            if newstring != '':
                newstring = newstring + char + data[z]
                z += 1
                continue
        continue
    return newstring

# --[ IRC Functions ]---------------------------------------------------------------------------------------------------

# privmsg_(server, target, message) ------------------------------------------------------------------------------------
# Scripting Function
# For sending PRIVMSG
# NOTE: modified this for duckhunt flight text
def privmsg_(server, target, message):
    global systemdata
    try:
        systemdata[server, 'sock'].send(b'PRIVMSG ' + target + b' :' + bytes(message, 'utf-8') + b'\r\n')
    # This was added for port-ability in duckhunt project, it allows message syntax to contain bytes b'data'
    # privmsg_(server, target, b'message text')
    except TypeError:
        systemdata[server, 'sock'].send(b'PRIVMSG ' + target + b' :' + message + b'\r\n')  # Added for duckhunt port
    # This is for an error that occurs when a plugin has a internal timer [?]
    # This is still being worked on and/or dealt with. [/]
    except OSError:
        systemdata[server, 'sock'].close()

# For sending NOTICE
def notice_(server, target, message):
    global systemdata
    try:
        systemdata[server, 'sock'].send(b'NOTICE ' + target + b' :' + bytes(message, 'utf-8') + b'\r\n')
    # This was added for port-ability in duckhunt project, it allows message syntax to contain bytes b'data'
    # privmsg_(server, target, b'message text')
    except TypeError:
        systemdata[server, 'sock'].send(b'NOTICE ' + target + b' :' + message + b'\r\n')  # Added for duckhunt port
    # This is for an error that occurs when a plugin has a internal timer [?]
    # This is still being worked on and/or dealt with. [/]
    except OSError:
        systemdata[server, 'sock'].close()

# def mode_(threadname, target, mode):

# def kick_(threadname, channel, user, kmsg=''):

# def topic_(threadname, channel, topicmsg):
