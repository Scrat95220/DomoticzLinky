#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (C) v1.0.0 2023-10-27 Scrat
"""Generates energy consumption JSON files from Enedis consumption data
collected via Conso API (https://conso.boris.sh/documentation).
"""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib.request
import ssl
import base64
import configparser
import os
import requests
import datetime
import logging
import json
from dateutil.relativedelta import relativedelta
from urllib.parse import urlencode

API_BASE_URI = 'https://conso.boris.sh/api/'

logLevel = "INFO"

base64string=""

userName = ""
password = ""
devicerowid = ""
pdl = ""
token = ""
nbDaysImported = 30
domoticzserver   = ""
domoticzusername = ""
domoticzpassword = ""

script_dir=os.path.dirname(os.path.realpath(__file__)) + os.path.sep

class LinkyServiceException(Exception):
    """Thrown when the webservice threw an exception."""
    pass

def domoticzrequest (url):
  global base64string

  context = ssl._create_unverified_context()
  request = urllib.request.Request(domoticzserver + url)
  if(domoticzusername != "" and domoticzpassword!= ""):
    base64string = base64.encodebytes(('%s:%s' % (domoticzusername, domoticzpassword)).encode()).decode().replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    
  try:
    logging.debug("Domoticz Request : \n" + request.full_url)  
    response = urllib.request.urlopen(request, context=context)
    logging.debug("Domoticz Response : \n" + response.read().decode('utf-8')) 
    return response.read()
  except urllib.error.HTTPError as e:
    print(e.__dict__)
    logging.error("Domoticz call - HttpError :"+str(e.__dict__)+'\n')
    exit()
  except urllib.error.URLError as e:
    print(e.__dict__)
    logging.error("Domoticz call - UrlError :"+str(e.__dict__)+'\n')
    exit()
  
# Date formatting 
def dtostr(date):
    return date.strftime("%Y-%m-%d")
    
def get_daily_consumption(start_date, end_date):
    session = requests.Session()
    resp_daily_consumption = session.get(API_BASE_URI + 'daily_consumption?prm=' + pdl + '&start=' + start_date + '&end=' + end_date, headers={'Authorization': 'Bearer ' + token})
    logging.debug("Get daily_consumption : \n" + resp_daily_consumption.text)
    if resp_daily_consumption.status_code != requests.codes.ok:
        print("Get daily_consumption call - error status :",resp_daily_consumption.status_code, '\n');
        logging.error("Get daily_consumption call - error status :",resp_daily_consumption.status_code, '\n')
        exit()
        
    return json.loads(resp_daily_consumption.text)
    
def get_consumption_max_power(start_date, end_date):
    session = requests.Session()
    resp_consumption_max_power = session.get(API_BASE_URI + 'consumption_max_power?prm=' + pdl + '&start=' + start_date + '&end=' + end_date, headers={'Authorization': 'Bearer ' + token})
    logging.debug("Get consumption_max_power : \n" + resp_consumption_max_power.text)
    if resp_consumption_max_power.status_code != requests.codes.ok:
        print("Get consumption_max_power call - error status :",resp_consumption_max_power.status_code, '\n');
        logging.error("Get consumption_max_power call - error status :",resp_consumption_max_power.status_code, '\n')
        exit()
        
    return json.loads(resp_consumption_max_power.text)
    
def update_counters(json_resp_daily_consumption, json_resp_consumption_max_power):
    # Updater counter setting for authorize History update
    args = {'type': 'command', 'param': 'setused', 'idx': devicerowid, 'switchtype' : 'SUBTYPE_VALUE', 'used': 'true', 'options': 'RGlzYWJsZUxvZ0F1dG9VcGRhdGU6dHJ1ZTtBZGREQkxvZ0VudHJ5OnRydWU='}
    url_update_counter_setting = '/json.htm?' + urlencode(args)
    domoticzrequest(url_update_counter_setting)      
    
    for releve in json_resp_daily_consumption['interval_reading']:
        daily_consumption_date = releve['date']
        conso = releve['value']
                            
        # Generate URLs, for historique
        logging.debug("Data to inject : " + str(conso) + ";0;0;0;0;0;" + daily_consumption_date)
        args = {'type': 'command', 'param': 'udevice', 'idx': devicerowid, 'nvalue' : 0, 'svalue': str(conso) + ";0;0;0;0;0;" + daily_consumption_date}
        url_historique = '/json.htm?' + urlencode(args)
        
        domoticzrequest(url_historique)   
    
    # Updater counter setting for authorize History update
    args = {'type': 'command', 'param': 'setused', 'idx': devicerowid, 'switchtype' : 'SUBTYPE_VALUE', 'used': 'true', 'options': 'RGlzYWJsZUxvZ0F1dG9VcGRhdGU6dHJ1ZQ=='}
    url_update_counter_setting = '/json.htm?' + urlencode(args)
    domoticzrequest(url_update_counter_setting)
    
    # Get datas for daily
    last_daily_consumption = json_resp_daily_consumption['interval_reading'][len(json_resp_daily_consumption['interval_reading'])-1]['value']
    logging.debug('Last daily consumption : ' + str(last_daily_consumption))
    last_consumption_max_power = json_resp_consumption_max_power['interval_reading'][len(json_resp_consumption_max_power['interval_reading'])-1]['value']
    logging.debug('Last consumption_max_power : ' + str(last_consumption_max_power))
    
    # Generate URLs, for daily
    logging.debug("Data to inject : " + str(last_daily_consumption) + ";0;0;0;" + str(last_consumption_max_power) + ";0")
    args = {'type': 'command', 'param': 'udevice', 'idx': devicerowid, 'nvalue' : 0, 'svalue': str(last_daily_consumption) + ";0;0;0;" + str(last_consumption_max_power) + ";0"}
    url_daily = '/json.htm?' + urlencode(args)
    domoticzrequest(url_daily)
    
    # Updater counter setting for authorize History update
    args = {'type': 'command', 'param': 'setused', 'idx': devicerowid, 'switchtype' : 'SUBTYPE_VALUE', 'used': 'true', 'options': 'RGlzYWJsZUxvZ0F1dG9VcGRhdGU6dHJ1ZTtBZGREQkxvZ0VudHJ5OnRydWU='}
    url_update_counter_setting = '/json.htm?' + urlencode(args)
    domoticzrequest(url_update_counter_setting)

    
def get_config():
    configuration_file = script_dir + '/domoticz_linky.cfg'
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(configuration_file)
    global logLevel
    global devicerowid
    global token
    global nbDaysImported
    global pdl
    global domoticzserver
    global domoticzusername
    global domoticzpassword
    
    logLevel = config['SETTINGS']['LOG_LEVEL']
    devicerowid = config['DOMOTICZ']['DOMOTICZ_ID']
    token = config['LINKY']['TOKEN']
    nbDaysImported = config['LINKY']['NB_DAYS_IMPORTED']
    pdl = config['LINKY']['PDL']
    domoticzserver   = config['DOMOTICZ_SETTINGS']['HOSTNAME']
    domoticzusername = config['DOMOTICZ_SETTINGS']['USERNAME']
    domoticzpassword = config['DOMOTICZ_SETTINGS']['PASSWORD']
    
    logging.debug("config : " + userName + "," + password + "," + devicerowid + "," + nbDaysImported + "," + domoticzserver + "," + domoticzusername + "," + domoticzpassword)
        

# Main script 
def main():
    logging.basicConfig(filename=script_dir + '/domoticz_linky.log', format='%(asctime)s %(message)s', filemode='w') 

    try:
        # Get Configuration
        logging.info("Get configuration")
        get_config()
        
        #Set log level
        if(logLevel == "INFO"):
            logging.getLogger().setLevel(logging.INFO)
        if(logLevel == "DEBUG"):
            logging.getLogger().setLevel(logging.DEBUG)
        if(logLevel == "ERROR"):
            logging.getLogger().setLevel(logging.ERROR)            
        
        today = datetime.date.today()
        start_date = dtostr(today - relativedelta(days=int(nbDaysImported)))
        end_date = dtostr(today)
        logging.debug('start_date: ' + start_date + "; end_date: " + end_date)
        
        logging.info("retrieving data...")
        #1st request- Get daily_consumption    
        json_resp_daily_consumption = get_daily_consumption(start_date, end_date)
        
        #2nd request- Get consumption_max_power       
        json_resp_consumption_max_power = get_consumption_max_power(start_date, end_date)

        # Update Counters Domoticz
        logging.info("Update Domoticz datas...")
        update_counters(json_resp_daily_consumption,json_resp_consumption_max_power)
                                             
        logging.info("got data!")
    except LinkyServiceException as exc:
        logging.error(exc)
        exit()

if __name__ == "__main__":
    main()
