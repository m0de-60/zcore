#! /usr/bin/python3
# Mode60 Ultra-beta ZeroOne
# ======================================================================================================================
# Title.............: 'zcore'
# Filename..........: zcore.py (main file)
# Version...........: 0.1x
# Author............: Neo Nemesis
# Description.......: Expandable, scriptable, modular and most importantly, customizable IRC Bot core.
#                     Multi-network/channel. Can load and run python modules [that are designed to run with this core].
#                     See sys_zcore.py for working example of a 'zcore System Module'
#                     visit website for more info on zcore plugin moudles
# Python Version....: 3.12.0
# Bot Files List....: zcore.py, sys_zcore.py, zcore.cnf
# ----------------------------------------------------------------------------------------------------------------------
# Imports...........:
from configparser import ConfigParser
from datetime import date
from datetime import datetime
import configparser
import socket
import ssl
import platform
import time
import threading
import asyncio
import os.path
import logging
# ----------------------------------------------------------------------------------------------------------------------
# Global data map
zcore = {}
# log_filename = './zcorelog.txt'
logging.basicConfig(filename='./zcorelog.txt', level=logging.DEBUG)  # For error and debug logging
zcore['corelog'] = 'on'  # turn 'on' for testing, otherwise 'off'
# ======================================================================================================================
# start_up()
# Main start up function. Builds data map from zcore.cnf and initiates network threads and starts main loop.
async def start_up():
    global zcore
    # start up process, building data map
    zprint(f'[*] START UP * Powered by zCore (System Info: python: version {platform.python_version()} - OpenSSL: {ssl.OPENSSL_VERSION})')
    zprint(f'[*] Current Date: {cdate()} Current Time: {ctime()}')
    time.sleep(0.3)
    # check to make sure zcore.cnf exists
    if os.path.isfile('./zcore.cnf') is False:
        zprint(f'[*] ERROR * Required system file "zcore.cnf" is not found in zcore directory. Shutting down...')
        exit()
    # python version check needed here ?
    # ------------------------------------------------------------------------------------------------------------------
    # this below is the bot's core data [zcore] -> zcore.cnf used across all threads
    # to change this data go to zcore.cnf [zcore]
    zcore['serverlist'] = cnfread('zcore.cnf', 'zcore', 'serverlist').lower()
    zcore['botmaster'] = cnfread('zcore.cnf', 'zcore', 'botmaster').lower()
    # zcore['botadmin'] = cnfread('zcore.cnf', 'zcore', 'botadmin').lower()
    zcore['pingtime'] = int(cnfread('zcore.cnf', 'zcore', 'pingtime'))
    zcore['sysmod'] = cnfread('zcore.cnf', 'zcore', 'system').lower()
    zcore['plugins'] = cnfread('zcore.cnf', 'zcore', 'plugins').lower()
    zcore['plugin'] = zcore['plugins'].split(',')
    zcore['s-mount'] = '0'  # For remote and terminal adding/removing system module
    zcore['p-mount'] = {}  # For remote and terminal adding/removing plugin module
    # ------------------------------------------========================================================================
    # MAIN PLUGIN CONTROL (no plugmods = False)
    zcore['plugmods'] = True
    # =======================================---------------------------------------------------------------------------
    # global use data (do not alter)
    zcore['keepalive'] = False
    zcore['sslref'] = ''
    zcore['mode'] = 'start'
    zcore['dump'] = ''
    # version hard code do not change ----------------------------------------------------------------------------------
    # !!!zcore module failure/errors will occur with error changes!!!
    zcore['version'] = '0.1x'
    zcore['versionid'] = 'Z3R00N3'
    zprint(f'[*] RUNNING * zCore version: {zcore['version']} by Neo Nemesis')
    # ------------------------------------------------------------------------------------------------------------------
    # Loading system module (if specified in zcore.cnf: [zcore] > system = modulename
    # ONLY 1 SYSTEM MODULE.
    # If no system module is being used, then zcore.cnf: [zcore] > system = 0
    # ------------------------------------------------------------------------------------------------------------------
    # No system module specified
    if zcore['sysmod'] == '0':
        zcore['system'] = '0'
        zprint(f'[*] No system module specified. Internal system disabled.')
    # ------------------------------------------------------------------------------------------------------------------
    # System module specified
    else:
        zprint(f'[*] Checking for system module {zcore['sysmod']}...')
        time.sleep(0.5)  # sure does
        # module filename.py exists
        if os.path.isfile('./' + zcore['sysmod'] + '.py') is True:
            zprint(f'[*] System Module found. Loading...')
            zcore['system'] = __import__(zcore['sysmod'])
            try:
                zcore['system'].system_init_(zcore['version'])
            except AttributeError:
                zcore['system'] = '0'
                zprint(f'[*] ERROR * Module failed to load: {zcore['sysmod']} is not recognized as a system module. System mode disabled.')
        # module filename.py does not exist
        else:
            zcore['system'] = '0'  # zcore['system'] = 'err1'  system module filename.py is missing
            zprint(f'[*] ERROR * System module {zcore['sysmod']}.py is not found. System mode disabled.')
    # ------------------------------------------------------------------------------------------------------------------
    # check for and load plugins
    # ------------------------------------------------------------------------------------------------------------------
    if zcore['plugins'] == '0':
        zprint(f'[*] 0 plugin modules specified. Plugin system disabled.')
        if zcore['system'] == '0':
            zprint(f'[*] Running in idle mode')
    else:
        zprint(f'[*] {len(zcore['plugin'])} plugin module(s) found.')
        plugint = zcore['plugins'].split(',')
        time.sleep(0.5)
        for x in range(len(zcore['plugin'])):
            if os.path.isfile('./' + zcore['plugin'][x] + '.py') is True:
                zprint(f'[*] Attempting to load: {zcore['plugin'][x]}')
                zcore['plugin'][x] = __import__(zcore['plugin'][x])
                try:
                    if zcore['sysmod'] != zcore['plugin'][x].system_req_():
                        zprint(f'[*] ERROR * System Module: Plugin Module {plugint[x]} requires System Module {zcore['plugin'][x].system_req_()}. Module skipped...')
                        zcore['plugin'][x] = '0'
                        continue
                except AttributeError:
                    zcore['dump'] = 0

                try:
                    zcore['plugin'][x].plugin_init_()
                except AttributeError:
                    zprint(f'[*] ERROR * Plugin module {plugint[x]} is not recognized as a plugin module.')
                    zcore['plugin'][x] = '0'
            else:
                zprint(f'[*] ERROR * Plugin module {plugint[x]}.py is not found.')
                zcore['plugin'][x] = '0'
            continue

    # ------------------------------------------------------------------------------------------------------------------
    # start up IRC connections
    # ------------------------------------------------------------------------------------------------------------------
    # this data pertains to each network specifically. [serverid] -> zcore.cnf
    zprint(f'[*] Preparing to connect to IRC network(s)...')
    time.sleep(1.5)  # not sure if really needed?
    p_server = zcore['serverlist'].split(',')
    for x in range(len(p_server)):
        # each server (p_server[x]=serverid) in zcore.cnf ([zcore]>serverlist) gets its own map and network thread
        # zcore['serverid', 'data']
        zcore[p_server[x], 'serverid'] = cnfread('zcore.cnf', p_server[x], 'serverid').lower()
        zcore[p_server[x], 'serveraddr'] = cnfread('zcore.cnf', p_server[x], 'serveraddr').lower()
        zcore[p_server[x], 'serverport'] = int(cnfread('zcore.cnf', p_server[x], 'serverport'))
        zcore[p_server[x], 'serverssl'] = cnfread('zcore.cnf', p_server[x], 'serverssl').lower()
        zcore[p_server[x], 'botname'] = cnfread('zcore.cnf', p_server[x], 'botname')
        zcore[p_server[x], 'botpass'] = cnfread('zcore.cnf', p_server[x], 'botpass')
        zcore[p_server[x], 'channels'] = cnfread('zcore.cnf', p_server[x], 'channels').lower()
        zcore[p_server[x], 'keepalive'] = time.time()
        zcore[p_server[x], 'connected'] = False
        zcore[p_server[x], 'lastlag'] = 'NA'
        # start network thread
        zcore[p_server[x], 'thread'] = threading.Thread(target=irc_connect, args=(p_server[x],), daemon=True)
        zcore[p_server[x], 'thread'].start()
        continue
    # ------------------------------------------------------------------------------------------------------------------
    # starts the main 'keep alive' loop when the above is finished
    await keep_alive()

# <-- End start_up() ===================================================================================================

# ======================================================================================================================
# zprint('message')
# Core screen printing and logging
def zprint(message):
    global zcore
    print(message)
    if zcore['corelog'] == 'on':
        logging.debug(message)
    return
# ======================================================================================================================
# re_connect(serverid):
# reconnects when a server connection is lost
async def re_connect(serverid):
    global zcore
    zcore[serverid, 'connected'] = False
    zcore[serverid, 'lastlag'] = 'NA'
    zcore[serverid, 'thread'] = ''
    zprint(f'[*] Reconnecting to {serverid} in 60 seconds...')
    time.sleep(60)
    zcore[serverid, 'keepalive'] = time.time()
    zcore[serverid, 'thread'] = threading.Thread(target=irc_connect, args=(serverid,), daemon=True)
    zcore[serverid, 'thread'].start()

# ======================================================================================================================
# irc_connect(serverid)
# Connection and loop start up procedure for specified network thread (serverid)
def irc_connect(serverid):
    global zcore
    zprint(f'[*] Opening connection to {serverid}...')
    # socket start up and connect
    zcore[serverid, 'sock'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # need to add try/except here for socket.gaierror and ssl.SSLEOFError
    try:
        zcore[serverid, 'sock'].connect((str(zcore[serverid, 'serveraddr']), int(zcore[serverid, 'serverport'])))
    except socket.gaierror or ssl.SSLEOFError:
        zprint(f'[*] Connection attempt to {serverid} failed. Attempting reconnection in 15 seconds...')
        time.sleep(15)
        asyncio.run(re_connect(serverid))
        return
    # SSL only
    if zcore[serverid, 'serverssl'] == 'yes':
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        zcore[serverid, 'sock'] = context.wrap_socket(zcore[serverid, 'sock'], server_hostname=zcore[serverid, 'serveraddr'])
    # Send USER, NICK and (optional) PASS to server.
    zcore[serverid, 'sock'].send(b'USER ' + bytes(str(zcore[serverid, 'botname']), 'utf-8') + b' zCore zCore :zCore (ZeroOne) ' + bytes(str(zcore['version']), 'utf-8') + b'\r\n')
    zcore[serverid, 'sock'].send(b'NICK ' + bytes(str(zcore[serverid, 'botname']), 'utf-8') + b'\r\n')
    if zcore[serverid, 'botpass'] != '0':
        zcore[serverid, 'sock'].send(b'PASS ' + bytes(str(zcore[serverid, 'botpass']), 'utf-8') + b'\r\n')
    # starts the socket loop in the network thread.
    zcore[serverid, 'connected'] = 'Try'
    try:
        asyncio.run(irc_loop(serverid))
    except:
        logging.exception('[---ERROR FOUND---]')  # For error tracebacks to zcorelog.txt
        raise
# <-- End irc_connect() ================================================================================================

# ======================================================================================================================
# irc_loop(threadname)
# asyncio irc socket loop (runs in each network thread)
async def irc_loop(threadname):
    global zcore
    while 1:
        if zcore['mode'] == 'shutdown' or zcore['mode'] == 'reboot' or zcore[threadname, 'connected'] is False:
            break
        # check if keep alive is still keeping alive
        if not zcore['keepalive']:
            await keep_alive()
        # --------------------------------------------------------------------------------------------------------------
        # main socket data receiving
        # because for some reason certain server SSL patterns cause random EOF (see exception at bottom of loop)
        zcore[threadname, 'recv'] = zcore[threadname, 'sock'].recv(2040)  # receiving
        zcore[threadname, 'data_line'] = zcore[threadname, 'recv'].splitlines()  # separation
        # parse socket data
        for x in range(len(zcore[threadname, 'data_line'])):
            zcore[threadname, 'data'] = zcore[threadname, 'data_line'][x].split(b' ')
            if len(zcore[threadname, 'data']) > 1:
                # --------------------------------------------------------------------------------------------------
                # server ping/pong and lag timer
                # received ping from server, send pong reply
                if zcore[threadname, 'data'][0] == b'PING':
                    zcore[threadname, 'keepalive'] = time.time()
                    zprint(f'[*] {threadname} ---> Ping? {zcore[threadname, 'data'][1]}')
                    zcore[threadname, 'sock'].send(b'PONG ' + zcore[threadname, 'data'][1] + b'\r\n')
                    zprint(f'[*] {zcore[threadname, 'botname']} ---> {threadname} Pong! {zcore[threadname, 'data'][1]}')
                    continue
                # received pong reply from ping sent to server
                # keep alive pong and lag timer
                if zcore[threadname, 'data'][1] == b'PONG':
                    zcore['keepalive', 'math'] = round(time.time() - zcore[threadname, 'keepalive'], 2)
                    zcore[threadname, 'lastlag'] = zcore['keepalive', 'math']
                    zprint(f'[*] {threadname} ---> PONG (KeepAlive) Lag: {zcore['keepalive', 'math']} seconds')
                    continue
                # --------------------------------------------------------------------------------------------------
                # connection successful, raw 001 welcome message
                if zcore[threadname, 'data'][1] == b'001':
                    zprint(f'[*] {threadname} connection successful.')
                    # send socket data to system module and/or plugins
                    socket_transfer(threadname, zcore[threadname, 'sock'])
                    zcore[threadname, 'connected'] = True
                    # join channels
                    zcore[threadname, 'chan'] = zcore[threadname, 'channels'].split(',')
                    for y in range(len(zcore[threadname, 'chan'])):
                        zprint(f'[*] {threadname} joining {zcore[threadname, 'chan'][y]}...')
                        zcore[threadname, 'sock'].send(b'JOIN ' + bytes(str(zcore[threadname, 'chan'][y]), 'utf-8') + b'\r\n')
                        continue
                    continue
                # ------------------------------------------------------------------------------------------------------
                # raw 433 :Nickname is already in use
                if zcore[threadname, 'data'][1] == b'433':
                    if zcore['mode'] != 'shutdown':
                        zcore['mode'] = 'shutdown'
                        zcore[threadname, 'sock'].close()
                        zprint(f'[*] {threadname} ERROR * Nickname already in use. Please edit the botname for {threadname} in zcore.cnf and restart the bot. Shutting down...')
                        break
                    if zcore['mode'] == 'shutdown':
                        zcore[threadname, 'sock'].close()
                        break
                # if zcore[threadname, 'data'][1] == b'433':
                #    zprint(f'[*] {threadname} ERROR * Nickname already in use. Switching to zCore_01. Use !reboot to reset.')
                #    zcore[threadname, 'sock'].send(b'NICK zCore_01\r\n')
                #    zcore[threadname, 'botname'] = 'zCore_01'
                #    continue
                # ------------------------------------------------------------------------------------------------------
                # PRIVMSG handling (also CTCP)
                if len(zcore[threadname, 'data']) > 2:
                    # --------------------------------------------------------------------------------------------------
                    # failsafe prints data to screen if no modules or plugins are loaded
                    if zcore['plugins'] == '0' and zcore['system'] == '0':
                        zprint(f'[*] {threadname} ---> {zcore[threadname, 'data_line'][x]}')
                    # --------------------------------------------------------------------------------------------------
                    if zcore[threadname, 'data'][1] == b'PRIVMSG':
                        # PRIVMSG :\x01 (CTCP)
                        # CTCP Version
                        zcore[threadname, 'rusername'] = b''
                        if zcore[threadname, 'data'][3].upper() == b':\x01VERSION\x01':
                            zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                            zprint(f'[*] {threadname} * {zcore[threadname, 'rusername'].decode()} ---> CTCP VERSION REQUEST')
                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'] + b' :\x01VERSION zCore (ZeroOne) version ' + bytes(str(zcore['version']), 'utf-8') + b' (Running: ' + bytes(str(zcore['versionid']), 'utf-8') + b')\x01\r\n')
                            continue
                        # CTCP Finger
                        if zcore[threadname, 'data'][3].upper() == b':\x01FINGER\x01':
                            zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                            zprint(f'[*] {threadname} * {zcore[threadname, 'rusername'].decode()} ---> CTCP FINGER REQUEST')
                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'] + b' :\x01FINGER zCore (ZeroOne) version ' + bytes(str(zcore['version']), 'utf-8') + b' (Running: ' + bytes(str(zcore['versionid']), 'utf-8') + b')\x01\r\n')
                            continue
                        # CTCP vid (zcore only) also works for CLIENTINFO
                        if zcore[threadname, 'data'][3].upper() == b':\x01VERSIONID\x01' or zcore[threadname, 'data'][3].upper() == b':\x01VID\x01' or zcore[threadname, 'data'][3].upper() == b':\x01CLIENTINFO\x01':
                            zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                            zprint(f'[*] {threadname} * {zcore[threadname, 'rusername'].decode()} ---> zcore VERSIONID REQUEST [VID]')
                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'] + b' :\x01VERSION zCore (ZeroOne)' + bytes(str(zcore['version']), 'utf-8') + b' by Neo Nemesis (C) Mode60 2024 - ' + bytes(str(zcore['versionid']), 'utf-8') + b' is powered by zCore a GNU 3.0 licensed FOSS python modular IRC bot core.\x01\r\n')
                            continue
                        # CTCP Ping
                        if zcore[threadname, 'data'][3].upper() == b':\x01PING':
                            zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                            zprint(f'[*] {threadname} * {zcore[threadname, 'rusername'].decode()} ---> CTCP PING {zcore[threadname, 'data'][4].decode()}')
                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'] + b' :\x01PING ' + zcore[threadname, 'data'][4] + b'\r\n')
                            continue
                        # ----------------------------------------------------------------------------------------------
                        # BotMaster core commands
                        zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                        zcore[threadname, 'dusername'] = zcore[threadname, 'rusername'].decode()
                        if zcore[threadname, 'dusername'].lower() in zcore['botmaster']:
                            # ------------------------------------------------------------------------------------------
                            # Botmaster Channel Commands
                            if b'#' in zcore[threadname, 'data'][2]:
                                # !shutdown
                                if zcore[threadname, 'data'][3].lower() == b':!shutdown':
                                    zprint(f'[*] Shutdown command issued by: {zcore[threadname, 'rusername']}')
                                    zcore['mode'] = 'shutdown'
                                    break
                                # !restart/!reboot
                                if zcore[threadname, 'data'][3].lower() == b':!restart' or zcore[threadname, 'data'][3].lower() == b':!reboot':
                                    zprint(f'[*] Reboot command issued by: {zcore[threadname, 'rusername']}')
                                    re_start()
                                    break
                                # !test (disable before release)
                                if zcore[threadname, 'data'][3].lower() == b':!test':
                                    zcore[threadname, 'sock'].send(b'PRIVMSG ' + zcore[threadname, 'data'][2] + b' :Testing 1 2 3!\r\n')
                                    continue
                            # ------------------------------------------------------------------------------------------
                            # Botmaster /privmsg commands
                            if b'#' not in zcore[threadname, 'data'][2] and len(zcore[threadname, 'data']) > 2:
                                zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                                zcore[threadname, 'rusername'] = zcore[threadname, 'rusername'].decode()
                                zcore[threadname, 'rusername'] = zcore[threadname, 'rusername'].lower()
                                # --------------------------------------------------------------------------------------
                                # /privmsg botname stats
                                if zcore[threadname, 'data'][3].lower() == b':stats':
                                    # zcore[threadname, 'rusername'] = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                                    # zcore[threadname, 'rusername'] = zcore[threadname, 'rusername'].decode()
                                    # zcore[threadname, 'rusername'] = zcore[threadname, 'rusername'].lower()
                                    if zcore[threadname, 'rusername'] in zcore['botmaster']:
                                        await stats_msg(threadname, zcore[threadname, 'rusername'])
                                    continue
                                # --------------------------------------------------------------------------------------
                                # /privmsg botname clear-err-log
                                # Completely clears zcorelog.txt
                                if zcore[threadname, 'data'][3].lower() == b':clear-err-log':
                                    err_log('clear')
                                    zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :Error log zcorelog.txt has been cleared.\r\n')
                                    zprint(f'[*] zcorelog.txt has been cleared by {zcore[threadname, 'rusername']} {cdate()} {ctime()}')
                                    continue
                                # /privmsg botname save-err-log <filename.txt>
                                # Save current zcorelog.txt as <filename.txt> for back up purposes
                                if zcore[threadname, 'data'][3].lower() == b':save-err-log':
                                    if len(zcore[threadname, 'data']) == 4:
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' save-err-log filename.txt\r\n')
                                        continue
                                    if len(zcore[threadname, 'data']) > 4:
                                        f_name = zcore[threadname, 'data'][4].decode()
                                        f_name = f_name.lower()
                                        if numtok(f_name, '.') != 2:
                                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' save-err-log filename.txt\r\n')
                                            continue
                                        if gettok(f_name, 1, '.') != 'txt':
                                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' save-err-log filename.txt\r\n')
                                            continue
                                        if os.path.isfile(f_name) is True:
                                            zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: File ' + f_name.encode() + b' already exists.\r\n')
                                            continue
                                        err_log('save', f_name)
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :Current error log file has been saved as ' + f_name.encode() + b' in the zCore directory.\r\n')
                                        zprint(f'[*] zcorelog.txt has been copied as {f_name} {cdate()} {ctime()}')
                                # --------------------------------------------------------------------------------------
                                # /privmsg botname mount-p modulename
                                if zcore[threadname, 'data'][3].lower() == b':mount-p':
                                    if len(zcore[threadname, 'data']) <= 4:
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' mount-p module_name\r\n')
                                        continue
                                    mountplug = zcore[threadname, 'data'][4].lower()
                                    mountplug = mountplug.decode()
                                    mount_p = mod_m(mountplug, 'mount-p')
                                    # p1 module is already mounted
                                    if mount_p == 'p1':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Mounting failed; Plugin Module ' + mountplug.encode() + b' is already in the Plugin Mount.\r\n')
                                        continue
                                    # p2 plugin module recognized, ok to mount
                                    if mount_p == 'p2':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :SUCCESS: Plugin Module ' + mountplug.encode() + b' successfully mounted to the Plugin Mount. Preparing to reboot.\r\n')
                                        time.sleep(0.75)
                                        re_start()
                                    # p3 plugin modile is not recognized
                                    if mount_p == 'p3':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Mounting failed; Module ' + mountplug.encode() + b' is not recognized as a Plugin Module.\r\n')
                                        continue
                                    # p4 plugin module not found
                                    if mount_p == 'p4':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Module ' + mountplug.encode() + b' not found.\r\n')
                                        continue
                                # --------------------------------------------------------------------------------------
                                # /privmsg botname unmount-p modulename
                                if zcore[threadname, 'data'][3].lower() == b':unmount-p':
                                    if len(zcore[threadname, 'data']) <= 4:
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' unmount-p module_name\r\n')
                                        continue
                                    mountplug = zcore[threadname, 'data'][4].lower()
                                    mountplug = mountplug.decode()
                                    mount_p = mod_m(mountplug, 'unmount-p')
                                    # p5 module is not loaded
                                    if mount_p == 'p5':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid input; Plugin Module ' + mountplug.encode() + b' is not mounted.\r\n')
                                        continue
                                    # p6 no plugins loaded
                                    if mount_p == 'p6':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Unmount failed; Plugin Mount is currently free.\r\n')
                                        continue
                                    if mount_p == 'p7':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :SUCCESS: Plugin Module ' + mountplug.encode() + b' successfully unmounted from the Plugin Mount. Preparing to reboot.\r\n')
                                        time.sleep(0.75)
                                        re_start()
                                # --------------------------------------------------------------------------------------
                                # /privmsg botname mount-s modulename
                                # module must already exist in the zCore directory
                                if zcore[threadname, 'data'][3].lower() == b':mount-s':
                                    if len(zcore[threadname, 'data']) <= 4:
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' mount-s module_name\r\n')
                                        continue
                                    mountname = zcore[threadname, 'data'][4].lower()
                                    mountname = mountname.decode()
                                    mount_s = mod_m(mountname, 'mount-s')
                                    # S1 module is already mounted
                                    if mount_s == 's1':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Mounting failed; System Module ' + mountname.encode() + b' is already in the System Mount.\r\n')
                                        continue
                                    # S2 there is already another module in the mount
                                    if mount_s == 's2':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Mounting failed; System Mount is in use by another module.\r\n')
                                        continue
                                    # S3 system module recognized, and ok to mount
                                    if mount_s == 's3':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :SUCCESS: System Module ' + mountname.encode() + b' successfully mounted to the System Mount. Preparing to reboot.\r\n')
                                        time.sleep(0.75)
                                        re_start()
                                    # S4 module is not recognized as a system module
                                    if mount_s == 's4':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Mounting failed; Module ' + mountname.encode() + b' is not recognized as a System Module.\r\n')
                                        continue
                                    # S5 module not found
                                    if mount_s == 's5':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: System Module ' + mountname.encode() + b' not found.\r\n')
                                        continue
                                if zcore[threadname, 'data'][3].lower() == b':unmount-s':
                                    if len(zcore[threadname, 'data']) <= 4:
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Invalid syntax; Use: /privmsg ' + zcore[threadname, 'botname'].encode() + b' unmount-s module_name\r\n')
                                        continue
                                    mountname = zcore[threadname, 'data'][4].lower()
                                    mountname = mountname.decode()
                                    mount_s = mod_m(mountname, 'unmount-s')
                                    if mount_s == 's6':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Unmount failed; System Mount is currently free.\r\n')
                                        continue
                                    if mount_s == 's7':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :ERROR: Legacy input; Incorrect System Module name.\r\n')
                                        continue
                                    if mount_s == 's8':
                                        zcore[threadname, 'sock'].send(b'NOTICE ' + zcore[threadname, 'rusername'].encode() + b' :SUCCESS: System Module ' + mountname.encode() + b' successfully unmounted from the System Mount. Preparing to reboot.\r\n')
                                        time.sleep(0.75)
                                        re_start()
                    # --------------------------------------------------------------------------------------------------
                    # send privmsg data thru system module and plugins
                        # ----------------------------------------------------------------------------------------------
                        # ACTION
                        if zcore[threadname, 'data'][3] == b':\x01ACTION':
                            # run data in system module
                            if zcore['system'] != '0':
                                # Determine if exct_ function is defined
                                try:
                                    await zcore['system'].exct_action(threadname, zcore[threadname, 'data_line'][x])
                                except AttributeError:
                                    zcore['dump'] = '0'  # Surely this is needed.
                            # run data in plugin module(s)
                            if zcore['plugins'] != '0':
                                for p in range(len(zcore['plugin'])):
                                    if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                        continue
                                    if zcore['plugin'][p] == 'err':
                                        zcore['plugin'][p] = 'E'
                                        zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                        continue
                                    elif zcore['plugin'][p] != 'err':
                                        try:
                                            await zcore['plugin'][p].evt_action(threadname, zcore[threadname, 'data_line'][x])
                                        except AttributeError:
                                            zcore['dump'] = '0'  # Of course
                                    continue
                            continue
                        # ----------------------------------------------------------------------------------------------
                        # PRIVMSG
                        else:
                            # run data in system module
                            if zcore['system'] != '0':
                                try:
                                    await zcore['system'].exct_privmsg(threadname, zcore[threadname, 'data_line'][x])
                                except AttributeError:
                                    zcore['dump'] = '0'  # Yep, is it faster?
                            # run data in plugin module(s)
                            if zcore['plugins'] != '0':
                                for p in range(len(zcore['plugin'])):
                                    if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                        continue
                                    if zcore['plugin'][p] == 'err':
                                        zcore['plugin'][p] = 'E'
                                        zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                        continue
                                    else:
                                        try:
                                            await zcore['plugin'][p].evt_privmsg(threadname, zcore[threadname, 'data_line'][x])
                                        except AttributeError:
                                            zcore['dump'] = '0'  # Of course
                                    continue
                            continue
                    # ------------------------------------------------------------------------------------------------------
                    # NOTICE handling
                    if zcore[threadname, 'data'][1] == b'NOTICE':
                        # run data in system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_notice(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # sure
                        # run data in plugin module(s)
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_notice(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue
                        continue
                    # --------------------------------------------------------------------------------------------------
                    # JOIN handling
                    if zcore[threadname, 'data'][1] == b'JOIN':
                        # run data in system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_join(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # experimental
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_join(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue
                        continue
                    # --------------------------------------------------------------------------------------------------
                    # PART handling
                    if zcore[threadname, 'data'][1] == b'PART':
                        # run data in system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_part(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # experimental
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_part(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue
                        continue
                    # --------------------------------------------------------------------------------------------------
                    # KICK handling
                    # b':Neo_Nemesis!~TheOne@th3.m4tr1x.h4ck3d.y0u KICK #testduck zcore :testing 1 2 3'
                    if zcore[threadname, 'data'][1] == b'KICK':
                        # system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_kick(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # hmm
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_kick(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # MODE handling
                    # User mode +v +o etc: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +v zcore'
                    # Channel mode +i, +s etc: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +i '
                    # Channel ban +b: b':Neo_Nemesis!~TheOne@hostmask.net MODE #TestWookie +b *!*@Test'
                    if zcore[threadname, 'data'][1] == b'MODE':
                        # system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_mode(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # surely this has caught on by now
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_action(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # TOPIC handling
                    # b':Neo_Nemesis!~TheOne@hostmask.net TOPIC #TestWookie :test'
                    if zcore[threadname, 'data'][1] == b'TOPIC':
                        # system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_topic(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_topic(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # NICK changes
                    # b':Testing!Mibbit@hostmask.net NICK :Test123'
                    if zcore[threadname, 'data'][1] == b'NICK':
                        # system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_nick(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_nick(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # QUIT handling
                    # b':Test123!Mibbit@hostmask.net QUIT :Client Quit'
                    # NEED TO ADD A CHECK FOR EXCESS FLOOD BY THE BOT!
                    if zcore[threadname, 'data'][1] == b'QUIT':
                        # Excess Flood
                        # if len(zcore[threadname, 'data']) >= 3 and zcore[threadname, 'data'][2].lower() == b':excess':
                        #   usr = gettok(zcore[threadname, 'data'][0], 0, b'!').replace(b':', b'')
                        #   usr = usr.decode()
                        #   if usr.lower() == zcore[threadname, 'botname'].lower():

                        # system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_quit(threadname, zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_quit(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # RAW numeric data
                    rawdata = zcore[threadname, 'data'][1].decode()
                    if rawdata.isnumeric() is True:
                        # run data in system module
                        if zcore['system'] != '0':
                            try:
                                await zcore['system'].exct_raw(threadname, zcore[threadname, 'data'][1], zcore[threadname, 'data_line'][x])
                            except AttributeError:
                                zcore['dump'] = '0'  # Still working?
                            continue
                        if zcore['plugins'] != '0':
                            for p in range(len(zcore['plugin'])):
                                if zcore['plugin'][p] == '0' or zcore['plugin'][p] == 'E':
                                    continue
                                if zcore['plugin'][p] == 'err':
                                    zcore['plugin'][p] = 'E'
                                    zprint(f'[*] ERROR * Plugin failure: {zcore['plugin'][p]} Plugin shut down.')
                                    continue
                                elif zcore['plugin'][p] != 'err':
                                    try:
                                        await zcore['plugin'][p].evt_raw(threadname, zcore[threadname, 'data_line'][x])
                                    except AttributeError:
                                        zcore['dump'] = '0'  # Of course
                                continue

                    # --------------------------------------------------------------------------------------------------
                    # Checking for broken lines and data errors in recv data from server
                    # system module only
                    if zcore['system'] != '0':
                        try:
                            await zcore['system'].exct_chk(threadname, zcore[threadname, 'data_line'][x])
                        except AttributeError:
                            zcore['dump'] = '0'  # yea
                        finally:
                            continue

                # ------------------------------------------------------------------------------------------------------
                # failsafe prints data to screen if no modules or plugins are loaded
                # if zcore['plugins'] == '0' and zcore['system'] == '0' and len(zcore[threadname, 'data']) > 2:
                #    zprint(f'[*] {threadname} ---> {zcore[threadname, 'data_line'][x]}')
                continue
        continue
    # ------------------------------------------------------------------------------------------------------------------
    # loop is only broken by exiting or connection loss, return will terminate thread for restarting
    if zcore['mode'] != 'shutdown' and zcore['mode'] != 'reboot':
        zprint(f'[*] ERROR * {threadname} connection has failed.')
        zcore[threadname, 'connected'] = False
        zcore[threadname, 'sock'].close()
    return
# <-- End irc_loop() ===================================================================================================

# ======================================================================================================================
# module_stop('serverid'):
# Stops any plugins on server and its channels in the event of a connection loss/interruption (OSError, SSLError)
def module_stop(server):
    global zcore

    # run thru the plugins
    for x in range(len(zcore['plugin'])):
        try:
            zcore['plugin'][x].plugin_stop_(server)
            continue
        except AttributeError:
            continue
    return

# ======================================================================================================================
# keep_alive()
# keeps program and IRC connections alive (i.e. this is a main loop)
async def keep_alive():
    global zcore
    zcore['keepalive'] = True
    server = zcore['serverlist'].split(',')
    zcore['sslref'] = time.time()
    # ------------------------------------------------------------------------------------------------------------------
    # main loop
    while 1:
        time.sleep(0.01)  # quick break then back to work
        if zcore['mode'] == 'shutdown' or zcore['mode'] == 'reboot':
            break
        for pc in range(len(server)):
            if zcore[server[pc], 'connected'] is False:
                continue
            # ----------------------------------------------------------------------------------------------------------
            # determines if any of the network threads need to be pinged.
            if round(time.time() - zcore[server[pc], 'keepalive']) >= zcore['pingtime']:
                if zcore[server[pc], 'connected'] is True or zcore[server[pc], 'connected'] == 'Try':
                    # as above in irc_loop() this is for random SSL EOF error handling (See exception below)
                    # need to add try/except for ssl errors and socket errors
                    zprint(f'[*] {zcore[server[pc], 'botname']} ---> {server[pc]} PING (KeepAlive)')
                    try:
                        zcore[server[pc], 'sock'].send(b'PING :' + bytes(str(zcore['versionid'].upper()), 'utf-8') + b'\r\n')
                        zcore[server[pc], 'keepalive'] = time.time()
                    except ssl.SSLError or socket.gaierror or ConnectionResetError or OSError:
                        zprint(f'[*] Error * Connection to {server[pc]} has been lost at {ctime()} on {cdate()}. Preparing for reconnection...')
                        zcore[server[pc], 'connected'] = False
                        zcore[server[pc], 'sock'].close()
                        module_stop(server[pc])
                        zcore[server[pc], 'thread'].join()
                        # time.sleep(10)
                        await re_connect(server[pc])
                continue
        continue
    # Loop end/exit ----------------------------------------------------------------------------------------------------
    zcore['keepalive'] = False
    if zcore['mode'] == 'reboot':
        await start_up()
    if zcore['mode'] == 'shutdown':
        shut_down()
        time.sleep(0.1)
        exit()
# <-- End keep_alive() =================================================================================================

# ======================================================================================================================
# socket_transfer(threadname, sock)
# transfers socket data to system module and/or plugins on init
def socket_transfer(threadname, sock):
    global zcore
    # system module
    if zcore['system'] != '0':
        zcore['system'].socket_stage(threadname, sock)
    # plugins
    # if zcore['plugins'] != '0':
    #    for p in range(len(zcore['plugin'])):
    #        if zcore['plugin'][p] != 'err':
    #            zcore['plugin'][p].socket_set(threadname, sock)
    #        continue

# ======================================================================================================================
# stats_msg(threadname, user)
# sends bot stats to user on threadname (BOTMASTER ONLY)
async def stats_msg(threadname, user):
    # ------------------------------------------------------------------------------------------------------------------
    # Assembling [zcore] info
    vr, vi, mm = zcore['version'], zcore['versionid'], zcore['mode']
    vr, vi, mm = 'Version: ' + vr, 'vID: ' + vi, 'Mode: ' + mm
    # [Python version: 3.12.0]
    pv = '[Python version: ' + platform.python_version() + ']'
    # [OpenSSL version]
    sl = '[' + ssl.OPENSSL_VERSION + ']'
    vs = '[zcore] ' + vr + ' | ' + vi + ' | ' + mm + ' ' + pv + ' ' + sl
    vs = vs.encode()
    # ------------------------------------------------------------------------------------------------------------------
    # [Network Data] server1id Lag: x.xx seconds | server2id Lag: x.xx seconds
    p_server = zcore['serverlist'].split(',')
    pl = ''
    for x in range(len(p_server)):
        if pl == '':
            pl = p_server[x] + ' Lag: ' + str(zcore[p_server[x], 'lastlag']) + ' seconds'
            continue
        else:
            pl = pl + ' | ' + p_server[x] + ' Lag: ' + str(zcore[p_server[x], 'lastlag']) + ' seconds'
            continue
    pl = '[Network Data] ' + pl
    pl = pl.encode()
    # ------------------------------------------------------------------------------------------------------------------
    # send the info to user
    ur = user.encode()
    zcore[threadname, 'sock'].send(b'NOTICE ' + ur + b' :' + vs + b'\r\n')
    zcore[threadname, 'sock'].send(b'NOTICE ' + ur + b' :' + pl + b'\r\n')
# <- End stats_msg() ===================================================================================================

# ======================================================================================================================
# shut_down()
# shuts down the bot and awaits for the main loop to exit
def shut_down():
    global zcore
    zcore['mode'] = 'shutdown'
    zprint(f'[*] Shutting down...')
    time.sleep(0.5)  # probably needed
    # plugin shut down
    if zcore['plugins'] != '0':
        for x in range(len(zcore['plugin'])):
            if zcore['plugin'][x] != '0' and zcore['plugin'][x] != 'E' and zcore['plugin'][x] != 'err':
                zcore['plugin'][x].plugin_exit_()
                zcore['plugin'][x] = '0'
            continue
    # system shut down
    if zcore['system'] != '0':
        zcore['system'].system_exit_()
        zcore['system'] = '0'
        time.sleep(0.25)
    # IRC shut down
    p_server = zcore['serverlist'].split(',')
    for x in range(len(p_server)):
        zcore[p_server[x], 'connected'] = False
        zcore[p_server[x], 'sock'].send(b'QUIT :(Powered by zCore)\r\n')
        zcore[p_server[x], 'sock'].close()
        zcore[p_server[x], 'thread'].join()
        zprint(f'[*] {p_server[x]} disconnected.')
        continue
    zprint(f'[*] Exit complete. Good-bye!')
    zprint(f'[*] Shut Down at: {cdate()} Time: {ctime()}')
    zcore = {}
# <- End shut_down() ===================================================================================================

# ======================================================================================================================
# re_start()
# disconnects from any connected networks and prepares for reboot from main loop.
def re_start():
    global zcore
    zcore['mode'] = 'reboot'
    zprint(f'[*] Rebooting...')
    zprint(f'[*] Reboot at: {cdate()} Time: {ctime()}')
    time.sleep(0.5)  # needed? maybe...
    p_server = zcore['serverlist'].split(',')
    for x in range(len(p_server)):
        if zcore[p_server[x], 'connected'] is True or zcore[p_server[x], 'connected'] == 'Try':
            zcore[p_server[x], 'connected'] = False
            zcore[p_server[x], 'sock'].send(b'QUIT :Bot rebooting (Powered by zCore)\r\n')
        continue
    time.sleep(0.5)  # Definitely needed...
# <- End re_start() ====================================================================================================

# ======================================================================================================================
# plugin_load_(spec)
# spec = init_load
# subject to change or be re-written
# checks zcore.cnf for listed modules and loads them performing the module plugin_init()
# planning to expand this to include more module handling than just 'init_load'
async def plugin_load_(spec):
    global zcore
    # ------------------------------------------------------------------------------------------------------------------
    # plug_mod('init_load')
    # initiate module check and load at start up only.
    if spec == 'init_load':
        time.sleep(0.75)  # just do it
        for x in range(len(zcore['plugin'])):
            # ------------------------------------------------------------------------------------------------------
            # verify that filename.py for plugin exists in script directory
            zprint(f'[*] Searching for plugin module: {zcore['plugin'][x]}...')
            # ------------------------------------------------------------------------------------------------------
            # file exists
            if os.path.isfile('./' + zcore['plugin'][x].lower() + '.py') is True:
                zprint(f'[*] Found {zcore['plugin'][x]}, attempting to load plugin module...')
                # import module[x]
                zcore['plugin'][x] = __import__(zcore['plugin'][x].lower())
                try:
                    zcore['plugin'][x].plugin_init_()
                # plugin is not recognized
                except AttributeError:
                    zcore['plugin'][x] = 'err'
                    zprint(f'[*] ERROR * Plugin module failed to load: Plugin not recognized.')
                # zprint(f'MNAME: {zcore['plugin'][x].systemdata['mname']}')
                finally:
                    continue
            # ------------------------------------------------------------------------------------------------------
            # file does not exist
            else:
                zprint(f'[*] ERROR * Plugin module failed to load: Unable to locate plugin module {zcore['plugin'][x]}.')
                zcore['plugin'][x] = 'err'
                continue
        # --------------------------------------------------------------------------------------------------------------
        # determine mode
        # if zcore['system'] != '0':
        #    zcore['mode'] = 'mod'
        #    zprint(f'[*] Running in modified system mode.')
        # else:
        #     zcore['mode'] = 'plugin'
        #    zprint(f'[*] Running in plugin mode.')
# <-- End plugin_load_() ===============================================================================================

# ======================================================================================================================
# Reading, writing and editing cnf files (for the core)
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
    config_object = ConfigParser()
    config_object.read(file)
    info = config_object[section]
    info[key] = data
    with open(file, 'w') as conf:
        config_object.write(conf)

# ======================================================================================================================
# Token handling
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

# Date and time --------------------------------------------------------------------------------------------------------
def cdate():
    to_day = date.today()
    return to_day.strftime("%B %d, %Y")

def ctime():
    now = datetime.now()
    return now.strftime("%H:%M:%S")
# ======================================================================================================================
# Error log clearing and saving feature
# err_log('clear') - Clears zcorelog.txt
# err_log('save', 'filename.txt') - Save current error log as filename.txt
def err_log(args, filename=''):
    if args == 'clear':
        open('zcorelog.txt', 'w').close()
        return 1
    if args == 'save':
        c_file = open('zcorelog.txt', 'r')
        n_file = open(filename, 'a')
        filelines = c_file.readlines()
        for x in range(len(filelines)):
            n_file.write(filelines[x])
            continue
        c_file.close()
        n_file.close()
        return 1
    return 0
# ======================================================================================================================
# Input controls (terminal)
# async def bm_input(args):
#    value = input('Text here > ')
#    print(value)
#    return

# ======================================================================================================================
# Controls for core and remote mounting and unmounting of system and plugin modules
# syntax mod_m('module name', 'mount-s,unmount-s,mount-p,unmount-p')
# returns a code message for core and remote command interpretation
def mod_m(modulename, args):
    global zcore
    # ------------------------------------------------------------------------------------------------------------------
    # mod_m('modulename', 'mount-s') - attempt to mount 'modulename' to system mount
    if args == 'mount-s':
# s1    # module is already loaded
        if zcore['sysmod'] == modulename.lower():
            return 's1'
# s2   # there is already another system module in the mount
        if zcore['sysmod'] != '0':
            return 's2'
# s3-5  # attempt to verify and mount
        if zcore['sysmod'] == '0':
            if os.path.isfile('./' + modulename.lower() + '.py') is True:
                zcore['s-mount'] = __import__(modulename.lower())
                try:
# s3				# system module recognized, and ok to mount and reboot
                    if zcore['s-mount'].system_call_() is True:
                        cnfwrite('zcore.cnf', 'zcore', 'system', modulename.lower())
                        return 's3'
# s4            # module is not recognized as a system module
                except AttributeError:
                    zcore['s-mount'] = '0'
                    return 's4'
# s5        # module not found
            else:
                return 's5'
    # ------------------------------------------------------------------------------------------------------------------
    # mod_m('modulename', 'unmount-s') - attempt to unmount 'modulename' from system mount
    if args == 'unmount-s':

# s6    # system mount is not in use
        if zcore['sysmod'] == '0':
            return 's6'
# s7    # incorrect module name
        if zcore['sysmod'] != modulename.lower():
            return 's7'
# s8    # system module unmounted
        cnfwrite('zcore.cnf', 'zcore', 'system', '0')
        return 's8'
    # ------------------------------------------------------------------------------------------------------------------
    # mod_m('modulename', 'mount-p') - attempt to mount 'modulename' to plugin mount
    if args == 'mount-p':
# p1    # plugin module is already mounted
        if modulename.lower() in zcore['plugins']:
            return 'p1'

# p2-4  # attempt to verify and mount
        if modulename.lower() not in zcore['plugin']:
            if os.path.isfile('./' + modulename.lower() + '.py') is True:
                zcore['p-mount'][modulename.lower()] = __import__(modulename.lower())
                try:
# p2                # plugin module recognized, okay to mount and reboot
                    if zcore['p-mount'][modulename.lower()].plugin_chk_() is True:
                        if zcore['plugins'] == '0':
                            cnfwrite('zcore.cnf', 'zcore', 'plugins', modulename.lower())
                        else:
                            dat = zcore['plugins'] + ',' + modulename.lower()
                            cnfwrite('zcore.cnf', 'zcore', 'plugins', dat)
                        return 'p2'
# p3            # plugin module is not recognized
                except AttributeError:
                    zcore['p-mount'][modulename.lower()] = '0'
                    return 'p3'
# p4        # plugin module not found
            else:
                return 'p4'
    # ------------------------------------------------------------------------------------------------------------------
    # mod_m(modulename, 'unmount-p') - attempt to remove 'modulename' from plugin mount
    if args == 'unmount-p':
# p5    # plugin module is not mounted
        if modulename.lower() not in zcore['plugins']:
            return 'p5'

# p6    # no plugins loaded
        if zcore['plugins'] == '0':
            return 'p6'

# p7   # unmount plugin module
        if numtok(zcore['plugins'], ',') == 1:
            cnfwrite('zcore.cnf', 'zcore', 'plugins', '0')
        else:
            dat = deltok(zcore['plugins'], modulename.lower(), ',')
            cnfwrite('zcore.cnf', 'zcore', 'plugins', dat)
        return 'p7'


# ======================================================================================================================
# Let's get booted up
try:
    asyncio.run(start_up())
except:
    if zcore != {} and zcore['mode'] != 'shutdown' and zcore['mode'] != 'reboot':
        # prints error info and exception traceback to zcorelog.txt
        logging.exception('[--=============--ERROR FOUND--=============--]')
        raise

# End <-- zcore v0.1x by Neo Nemesis [Mode60] ==========================================================================