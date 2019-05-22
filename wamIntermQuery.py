#This function reads a grib file using cfgrib and xarray and
#then queries attribute fields depending on the times and
#location (latitude and longitude).
#
#Brian Scanlon, Galway, 2019

import cfgrib
import pandas as pd
import numpy as np
ncFile = 'oceanWave_cop_climate_2018_Nov_01_to_02.nc'

#gribFile = 'oceanWave_cop_climate_2018_Nov_01_to_02.grib'
gribFile = '20181002_20181009.grib'
LatLonTimeFile = 'ShipTrack.csv'


def QueryGrib(gribFile,LatLonTimeFile,filterKeys={'dataType':'an','numberOfPoints':65160},ignoreList=['number','time','step'],DistanceLim=1,TimeDelayLim=6,QueryColumns=['time','lat','lon']):
	try:
		#Load GRIB:
		#ds = xarray.open_dataset(gribFile, engine='cfgrib')
		ds = cfgrib.open_file(gribFile,filter_by_keys=filterKeys)
		#Load Query file (comma separated; time, lon, lat):
		Queries = pd.read_csv(LatLonTimeFile,names=QueryColumns)
	except:
		print('Error loading GRIB or Query files, ')
		return -1
	else:
		#Extract frame data:
		Glat = list(ds.variables['latitude'].data)   #list(ds.latitude.data)
		Glon = list(ds.variables['longitude'].data-180)    #list(ds.longitude.data)
		Gtime = list(ds.variables['time'].data)    # list((ds.time.data).astype(float))/1e9 #we convert implicitly from np.datetime64 to timestamp!
		#Extract list of variables:
		gribVariables = ds.variables.keys()
		FRM = {}
		#
		dimsLogged=False
		for key in gribVariables:   #load the Grib Variables into memory one by one!
			if key not in ignoreList:  #Leaev open the possibility for a ignoreList to ignore specific keys
				try:
					keyData = ds.variables[key].data # try loading the data:
				except:
					print('failed to load variable {}'.format(key))
				else:
					for i in range(len(Queries)): # cycle through the number of queries!
						#find the closest (here we find the closest neighbor in the three dimensions (latitude, longitude and time)!
						iLat,dLat = find_nearest(Queries.lat[i],Glat)
						iLon,dLon = find_nearest(Queries.lon[i],Glon)
						iTime,dTime = find_nearest(float(Queries.time[i]),Gtime)
						#
						NearingDist = np.sqrt(dLat*dLat + dLon*dLon)
						#
						if not dimsLogged:
							FRM = MisterAssign(FRM,'DistFrmGrdPnt',NearingDist)	
							FRM = MisterAssign(FRM,'TimeOffset',dTime)	
						if NearingDist <= DistanceLim and dTime <=TimeDelayLim:
							try:
								if len(ds.dimensions.keys())==4:
									bufr = keyData[:,iTime,iLat,iLon]
									bufr[bufr==keyData.missing_value]=np.nan #remove any missing values!
									val = bufr.mean()	
								else:
									val = keyData[iTime,iLat,iLon]
								if val == 9999:
									val= np.nan
							except:
								val = np.nan
						else:
							val = np.nan
						#Assign value
						FRM = MisterAssign(FRM,key,val)
					dimsLogged=True
		return FRM





def MisterAssign(FRM,key,val):
	if key not in FRM:
		FRM[key]=[]
	FRM[key].append(val)
	return FRM


def find_nearest(array, value):
	array = np.asarray(array)
	distance = np.abs(array - value)
	idx = (distance).argmin()
	shortestDistance = min(distance)
	return (idx,shortestDistance)
'''
def npDT_to_timestampList(npDT64):
	OUT=[]
	for dt in npDT64:
		OUT.append()'''