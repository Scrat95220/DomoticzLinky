# DomoticzLinky
Import data from Enedis to Domoticz
This script use the bridge "Conso API" (https://github.com/bokub/conso-api)

As the quota via the bridge is limited, please execute the script only one time by day.

# create a device in Domoticz
- In Domoticz, go to hardware, create a virtual "P1 smart meter".

## modules to install - linux

    sudo apt-get install python3 python3-dateutil python3-requests
    git clone https://github.com/Scrat95220/DomoticzLinky.git
	
### rename configuration file, change settings

    cp _domoticz_linky.cfg domoticz_linky.cfg
    nano domoticz_linky.cfg

and change:

	[LINKY]
	TOKEN=
	PDL=
	NB_DAYS_IMPORTED=30

	[DOMOTICZ]
	DOMOTICZ_ID=

	[DOMOTICZ_SETTINGS]
	HOSTNAME=http://localhost:8080
	USERNAME =
	PASSWORD =
	

Where:
	TOKEN correspond to the value of the token return by this authorization : https://conso.boris.sh/api/auth
	PDL correspond to your "Point de Livraison" Enedis
	NB_DAYS_IMPORTED correspond to the number of days to import 
	DOMOTICZ_ID is id device on domoticz
	
Configuration file will not be deleted in future updates.


## Add to your cron tab (with crontab -e) for example a execution everut days at 08:30AM:

    8 30 * * * python3 /home/pi/domoticz/DomoticzLinky/linky.py
	
## OR add a Timer DZevents scripts in Domoticz like :
	return {
	on = {
		timer = {
			'at xx:xx:xx',					-- specific time
		}
	},
	logging = {
		level = domoticz.LOG_INFO,
		marker = 'template',
	},
	execute = function(domoticz, timer)
		domoticz.log('Timer event was triggered by ' .. timer.trigger, domoticz.LOG_INFO)
		print("Launch Linky")
        os.execute('python3 /home/pi/domoticz/scripts/python/DomoticzLinky/linky.py')
	end
}