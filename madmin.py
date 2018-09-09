# -*- coding: utf-8 -*-

import threading
import logging
import time
from flask import (Flask, abort, jsonify, render_template,
                   request, make_response,
                   send_from_directory, send_file, redirect)
from walkerArgs import parseArgs
from db.dbWrapper import DbWrapper
import sys
import json
import os, glob, platform
import re
import datetime
from time import gmtime, strftime
from shutil import copyfile

app = Flask(__name__)
sys.setdefaultencoding('utf8')

log = logging.getLogger(__name__)

args = parseArgs()

dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname,
                      args.timezone)

def activate_job():
    def run_job():
        try:
            while True:
                time.sleep(120)
                log.debug('MADmin: Heartbeat...')
        except KeyboardInterrupt:
            pass
            

    thread = threading.Thread(target=run_job)
    thread.start()

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response


@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

@app.route('/raids', methods=['GET'])
def raids():
    return render_template('raids.html')
    
@app.route('/gyms', methods=['GET'])
def gyms():
    return render_template('gyms.html')

@app.route('/unknown', methods=['GET'])
def unknown():
    return render_template('unknown.html')

@app.route("/submit_hash")
def submit_hash():
    hash = request.args.get('hash')
    id = request.args.get('id')
    if dbWrapper.insertHash(hash, 'gym', id, '999'):
        
        for file in glob.glob("www_hash/unkgym_*" + str(hash) + ".jpg"):
            copyfile(file, 'www_hash/gym_0_0_' + str(hash) + '.jpg')
            os.remove(file)
            
        return redirect("/unknown", code=302)

@app.route("/near_gym")
def near_gym():
    nearGym = []
    with open('gym_info.json') as f:
        data = json.load(f)
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return 'Missing Argument...'
    closestGymIds = dbWrapper.getNearGyms(lat, lon, 123, 1)
    for closegym in closestGymIds:
        
        gymid = str(closegym[0])
        dist = str(closegym[1])
        gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'
        
        name = 'unknown'
        lat = '0'
        lon = '0'
        url = '0'
        description = ''
        
        if str(gymid) in data:
            name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
            lat = data[str(gymid)]["latitude"]
            lon = data[str(gymid)]["longitude"]
            if data[str(gymid)]["description"]:
                description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")
        
        ngjson = ({'id': gymid, 'dist': dist, 'name': name, 'lat': lat, 'lon': lon, 'description': description, 'filename': gymImage})
        nearGym.append(ngjson)
 
    return jsonify(nearGym)
    
@app.route("/delete_hash")
def delete_hash():
    nearGym = []
    hash = request.args.get('hash')
    type = request.args.get('type')
    redi = request.args.get('redirect')
    if not hash or not type:
        return 'Missing Argument...'
        
    dbWrapper.deleteHashTable('"' + str(hash) + '"', type, 'in', 'hash')
    for file in glob.glob("www_hash/*" + str(hash) + ".jpg"):
        os.remove(file)
 
    return redirect('/' + str(redi), code=302)

@app.route("/delete_file")
def delete_file():
    nearGym = []
    hash = request.args.get('hash')
    type = request.args.get('type')
    redi = request.args.get('redirect')
    if not hash or not type:
        return 'Missing Argument...'
        
    for file in glob.glob("www_hash/*" + str(hash) + ".jpg"):
        os.remove(file)
 
    return redirect('/' + str(redi), code=302)

@app.route("/get_gyms")
def get_gyms():
    gyms = []
    with open('gym_info.json') as f:
        data = json.load(f)
    for file in glob.glob("www_hash/gym_*.jpg"):
        unkfile = re.search('gym_(-?\d+)_(-?\d+)_((?s).*)\.jpg', file)
        hashvalue = (unkfile.group(3))
        
        _gymid = dbWrapper.checkForHash(str(hashvalue), 'gym', 1)
        gymid = _gymid[1]
        count = _gymid[3]

        creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')

        name = 'unknown'
        lat = '0'
        lon = '0'
        url = '0'
        description = ''
        
        gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'

        if str(gymid) in data:
            name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
            lat = data[str(gymid)]["latitude"]
            lon = data[str(gymid)]["longitude"]
            if data[str(gymid)]["description"]:
                description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")

        gymJson = ({'id': gymid, 'lat': lat, 'lon': lon, 'hashvalue': hashvalue, 'filename': file, 'name': name, 'description': description, 'gymimage': gymImage, 'count': count, 'creation': creationdate })
        gyms.append(gymJson)

    return jsonify(gyms) 
    
@app.route("/get_raids")
def get_raids():
    raids = []
    eggIdsByLevel = [1, 1, 2, 2, 3]
    with open('gym_info.json') as f:
        data = json.load(f)
    for file in glob.glob("www_hash/raid_*.jpg"):
        unkfile = re.search('raid_(-?\d+)_(-?\d+)_((?s).*)\.jpg', file)
        hashvalue = (unkfile.group(3))
        
        raidid = dbWrapper.checkForHash(str(hashvalue), 'raid', 1)
        raidjson = raidid[1]
        count = raidid[3]
        
        raidHash_ = decodeHashJson(raidjson)
        gymid = raidHash_[0]
        lvl = raidHash_[1]
        mon = int(raidHash_[2])
        mon = "%03d"%mon
        
        if mon == '000':
            type = 'egg'
            monPic = ''
        else:
            type = 'mon'
            monPic = '/asset/pokemon_icons/pokemon_icon_' + mon + '_00.png'
            
        eggId = eggIdsByLevel[int(lvl) - 1]
        if eggId == 1:
            eggPic = '/asset/static_assets/png/ic_raid_egg_normal.png'
        if eggId == 2:
            eggPic = '/asset/static_assets/png/ic_raid_egg_rare.png'
        if eggId == 3:
            eggPic = '/asset/static_assets/png/ic_raid_egg_legendary.png'
            
        

        creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')

        name = 'unknown'
        lat = '0'
        lon = '0'
        url = '0'
        description = ''
        
        gymImage = 'gym_img/_' + str(gymid)+ '_.jpg'

        if str(gymid) in data:
            name = data[str(gymid)]["name"].replace("\\", r"\\").replace('"', '')
            lat = data[str(gymid)]["latitude"]
            lon = data[str(gymid)]["longitude"]
            if data[str(gymid)]["description"]:
                description = data[str(gymid)]["description"].replace("\\", r"\\").replace('"', '').replace("\n", "")

        raidJson = ({'id': gymid, 'lat': lat, 'lon': lon, 'hashvalue': hashvalue, 'filename': file, 'name': name, 'description': description, 'gymimage': gymImage, 'count': count, 'creation': creationdate, 'level': lvl, 'mon': mon, 'type': type, 'eggPic': eggPic, 'monPic': monPic })
        raids.append(raidJson)

    return jsonify(raids) 

@app.route("/get_unknows")
def get_unknows():
    unk = []
    for file in glob.glob("www_hash/unkgym_*.jpg"):
        unkfile = re.search('unkgym_(-?\d+\.\d+)_(-?\d+\.\d+)_((?s).*)\.jpg', file)
        creationdate = datetime.datetime.fromtimestamp(creation_date(file)).strftime('%Y-%m-%d %H:%M:%S')
        lat = (unkfile.group(1))
        lon = (unkfile.group(2))
        hashvalue = (unkfile.group(3))
        hashJson = ({'lat': lat, 'lon': lon,'hashvalue': hashvalue, 'filename': file, 'creation': creationdate})
        unk.append(hashJson)

    return jsonify(unk)   

@app.route('/gym_img/<path:path>', methods=['GET'])
def pushGyms(path):
    return send_from_directory('gym_img', path)

@app.route('/www_hash/<path:path>', methods=['GET'])
def pushHashes(path):
    return send_from_directory('www_hash', path)
    
@app.route('/match_unknows', methods=['GET'])
def match_unknows():
    hash = request.args.get('hash')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    return render_template('match_unknown.html', hash = hash, lat = lat, lon = lon)

@app.route('/asset/<path:path>', methods=['GET'])
def pushAssets(path):
    return send_from_directory(args.pogoasset, path)    


def decodeHashJson(hashJson):
    data = json.loads(hashJson)
    raidGym = data['gym']
    raidLvl = data["lvl"]
    raidMon = data["mon"]

    return raidGym, raidLvl, raidMon
    
def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)

    