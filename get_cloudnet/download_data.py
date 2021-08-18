#!/usr/bin/python3
'''
Download Cloudnet data from Pangaea using urllib
'''
import datetime as dt
import urllib.request
import urllib.error

url_reff_ice    = "https://hs.pangaea.de/model/GriescheH-etal_2020/MIRA_PS106_V2/{:04d}{:02d}{:02d}_polarstern_r-eff-ice.nc"
url_reff_Frisch = "https://hs.pangaea.de/model/GriescheH-etal_2020/LP_r-eff_PS106_V2/{:04d}{:02d}{:02d}_polarstern_r_eff_Frisch2002.nc"
url_lwc         = "https://hs.pangaea.de/model/GriescheH-etal_2020/LWC_PS106_V2/{:04d}{:02d}{:02d}_polarstern_lwc-scaled-adiabatic.nc" 
url_iwc         = "https://hs.pangaea.de/model/GriescheH-etal_2020/IWC_PS106_V2/{:04d}{:02d}{:02d}_polarstern_iwc-Z-T-method.nc"

date = dt.datetime(2017, 5, 24)
while date < dt.datetime(2017, 7, 19):
    
    ## Download lwc data
    url = url_lwc.format(date.year, date.month, date.day)
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        pass
    else:
        data = response.read()
        with open('lwc_{:02d}_{:02d}_{:04}.nc'.format(date.month, date.day, date.year), 'wb') as fobj:
            fobj.write(data)
            
    ## Download iwc data
    url = url_iwc.format(date.year, date.month, date.day)
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        pass
    else:
        data = response.read()
        with open('iwc_{:02d}_{:02d}_{:04}.nc'.format(date.month, date.day, date.year), 'wb') as fobj:
            fobj.write(data)

    ## Download reff Frisch data
    url = url_reff_Frisch.format(date.year, date.month, date.day)
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        pass
    else:
        data = response.read()
        with open('reff_Frisch_{:02d}_{:02d}_{:04}.nc'.format(date.month, date.day, date.year), 'wb') as fobj:
            fobj.write(data)
            
    ## Download reff ice data
    url = url_reff_ice.format(date.year, date.month, date.day)
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        pass
    else:
        data = response.read()
        with open('reff_ice_{:02d}_{:02d}_{:04}.nc'.format(date.month, date.day, date.year), 'wb') as fobj:
            fobj.write(data)
    date += dt.timedelta(days=1)