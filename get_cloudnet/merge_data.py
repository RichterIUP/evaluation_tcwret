#!/usr/bin/python3

import sys
import netCDF4 as nc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime as dt
from scipy.interpolate import interp1d
from pysolar.solar import *

def main(month, day, year=2017):
    path = "./"
    fname_lwc = "lwc_{:02d}_{:02d}_{:04}.nc".format(month, day, year)#time, height, latitude, longitude, lwc, lwc_error, lwc_retrieval_status, lwp, lwp_error
    #lwc_retrieval_status
    #1: Reliable retrieval 
    #2: Adiabatic retrieval where cloud top has been adjusted to match liquid water path from microwave radiometer because layer is not detected by radar
    #3: Adiabatic retrieval: new cloud pixels where cloud top has been adjusted to match liquid water path from microwave radiometer because layer is not detected by radar
    #4: No retrieval: either no liquid water path is available or liquid water path is uncertain
    #5: No retrieval: liquid water layer detected only by the lidar and liquid water path is unavailable or uncertain: cloud top may be higher than diagnosed cloud top since lidar signal has been attenuated
    #6: Rain present: cloud extent is difficult to ascertain and liquid water path also uncertain
    with nc.Dataset(os.path.join(path, fname_lwc)) as f:
        time = f.variables['time'][:]
        time_hours = time
        time_np_lwc = []
        for ii in range(time.size):
            sec = int(np.round(time[ii]*3600))
            time_np_lwc.append(np.timedelta64(sec, 's')+np.datetime64("2017-{:02d}-{:02d}T00:00:00".format(month, day)))
        time_np_lwc = np.array(time_np_lwc)
        height = f.variables['height'][:]
        latitude = f.variables['latitude'][:]
        longitude = f.variables['longitude'][:]
        lwc = f.variables['lwc'][:]
        lwc_error = f.variables['lwc_error'][:]
        lwc_st = f.variables['lwc_retrieval_status'][:]
        lwp = f.variables['lwp'][:]
        lwp_err = f.variables['lwp_error'][:]
    dz = np.diff(height)
    dz = np.concatenate((dz, [0]))
    lwp_lay = lwc * dz

    fname_iwc = "iwc_{:02d}_{:02d}_{:04}.nc".format(month, day, year)#time, height, iwc, iwc_bias, iwc_error, iwc_retrieval_status
    #iwc_retrieval_status
    #1: Reliable retrieval
    #2: Unreliable retrieval due to uncorrected attenuation from liquid water below the ice (no liquid water path measurement available)
    #3: Retrieval performed but radar corrected for liquid attenuation using radiometer liquid water path which is not always accurate
    #4: Ice detected only by the lidar
    #5: Ice detected by radar but rain below so no retrieval performed due to very uncertain attenuation
    #6: Clear sky above rain, wet-bulb temperature less than 0degC: if rain attenuation were strong then ice could be present but undetected
    #7: Drizzle or rain that would have been classified as ice if the wet-bulb temperature were less than 0degC: may be ice if temperature is in error
    with nc.Dataset(os.path.join(path, fname_iwc)) as f:
        #print(f.variables)
        iwc = f.variables['iwc'][:]
        iwc_error = f.variables['iwc_error'][:]
        iwc_bias = f.variables['iwc_bias'][:]
        iwc_st = f.variables['iwc_retrieval_status'][:]
    iwp_lay = iwc * dz
    fname_rliq = "reff_Frisch_{:02d}_{:02d}_{:04}.nc".format(month, day, year)#time, height, r_eff_Frisch, r_eff_Frisch_error, retrieval_status
    with nc.Dataset(os.path.join(path, fname_rliq)) as f:
        #print(f.variables)
        reff = f.variables['r_eff_Frisch'][:]
        reff_error = f.variables['r_eff_Frisch_error'][:]
        reff_st = f.variables['retrieval_status'][:]
    #retrieval_status:
    #1: Reliable retrieval.
    #2: Mix of drops and ice: Droplets and ice crystals coexist within pixel. Z may be biased by large crystals.
    #3: Precipitation in profile: Drizzle and rain affects LWP retrieval of MWR but also the target reflectivity.
    #4: Surrounding ice: Less crucial! Ice crystals in the vicinity of a droplet pixel may also bias its reflectivity.
    
    fname_rice = "reff_ice_{:02d}_{:02d}_{:04}.nc".format(month, day, year)#time, height, reff_ice, reff_ice_error, reff_ice_retrieval_status
    with nc.Dataset(os.path.join(path, fname_rice)) as f:
        #print(f.variables)
        reff_ice = f.variables['reff_ice'][:]
        reff_ice_error = f.variables['reff_ice_error'][:]
        reff_ice_st = f.variables['reff_ice_retrieval_status'][:]
    #reff_ice_retrieval_status:
    #1: Reliable retrieval
    #2: Unreliable retrieval due to uncorrected attenuation from liquid water below the ice (no liquid water path measurement available)
    #3: Retrieval performed but radar corrected for liquid attenuation using radiometer liquid water path which is not always accurate
    #4: Ice detected only by the lidar
    #5: Ice detected by radar but rain below so no retrieval performed due to very uncertain attenuation
    #6: Clear sky above rain, wet-bulb temperature less than 0degC: if rain attenuation were strong then ice could be present but undetected
    #7: Drizzle or rain that would have been classified as ice if the wet-bulb temperature were less than 0degC: may be ice if temperature is in error

    with nc.Dataset("cnet_{:02d}_{:02d}.nc".format(month, day), "w") as f:
        f.createDimension("const", 1)
        f.createDimension("level", height.size)
        f.createDimension("time", time_hours.size)

        time = f.createVariable("datetime", "f8", ("time", ))
        time.units = "hours since 2017-{:02d}-{:02d}".format(month, day)
        time[:] = time_hours[:]

        height_out = f.createVariable("height", "f8", ("level", ))
        height_out.units = "m"
        height_out[:] = height[:]

        lwc_out = f.createVariable("liquid_water_content", "f8", ("time", "level", ))
        lwc_out.units = "gm-3"
        lwc_out.comment ="This variable was calculated for the profiles where the 'categorization' data has diagnosed that liquid water is present and liquid water path is available from a coincident microwave radiometer. The model temperature and pressure were used to estimate the theoretical adiabatic liquid water content gradient for each cloud base and the adiabatic liquid water content is then scaled so that its integral matches the radiometer measurement so that the liquid water content now follows a quasi-adiabatic profile. If the liquid layer is detected by the lidar only, there is the potential for cloud top height to be underestimated and so if the adiabatic integrated liquid water content is less than that measured by the microwave radiometer, the cloud top is extended until the adiabatic integrated liquid water content agrees with the value measured by the microwave radiometer. Missing values indicate that either 1) a liquid water layer was diagnosed but no microwave radiometer data was available, 2) a liquid water layer was diagnosed but the microwave radiometer data was unreliable; this may be because a melting layer was present in the profile, or because the retrieved lwp was unphysical (values of zero are not uncommon for thin supercooled liquid layers), or 3) that rain is present in the profile and therefore, the vertical extent of liquid layers is difficult to ascertain."
        lwc_out[:] = lwc[:] * 1e3

        lwc_err_out = f.createVariable("liquid_water_content_error", "f8", ("time", "level", ))
        lwc_err_out.units = "dB"
        lwc_err_out.comment = 'This variable is an estimate of the random error in liquid water content due to the uncertainty in the microwave radiometer liquid water path retrieval and the uncertainty in cloud base and/or cloud top height. This is associated with the resolution of the grid used, 31 m, which can affect both cloud base and cloud top. If the liquid layer is detected by the lidar only, there is the potential for cloud top height to be underestimated. Similarly, there is the possibility that the lidar may not detect the second cloud base when multiple layers are present and the cloud base will be overestimated. It is assumed that the error contribution arising from using the model temperature and pressure at cloud base is negligible.'

        lwc_st_out = f.createVariable('liquid_water_content_status', 'i4', ('time', 'level', ))
        lwc_st_out.comment = 'This variable describes whether a retrieval was performed for each pixel, and its associated quality, in the form of 6 different classes. The classes are defined in the definition and long_definition attributes. The most reliable retrieval is that when both radar and lidar detect the liquid layer, and microwave radiometer data is present, indicated by the value 1. The next most reliable is when microwave radiometer data is used to adjust the cloud depth when the radar does not detect the liquid layer, indicated by the value 2, with a value of 3 indicating the cloud pixels that have been added at cloud top to avoid the profile becoming superadiabatic. A value of 4 indicates that microwave radiometer data were not available or not reliable (melting level present or unphysical values) but the liquid layers were well defined.  If cloud top was not well defined then this is indicated by a value of 5. The full retrieval of liquid water content, which requires reliable liquid water path from the microwave radiometer, was only performed for classes 1-3. No attempt is made to retrieve liquid water content when rain is present; this is indicated by the value 6.'
        lwc_st_out.definition = '0: No liquid water\n1: Reliable retrieval\n2: Adiabatic retrieval: cloud top adjusted\ņ3: Adiabatic retrieval: new cloud pixel\n4: Unreliable lwp: no retrieval\n5: Unreliable lwp/cloud boundaries: no retrieval\n6: Rain present: no retrieval'
        lwc_st_out[:] = lwc_st[:]

        lwp_lay_out = f.createVariable('liquid_water_path_per_layer', 'f8', ('time', 'level', ))
        lwp_lay_out.units = 'gm-2'
        lwp_lay_out[:] = lwp_lay[:] * 1e3

        iwp_lay_out = f.createVariable('ice_water_path_per_layer', 'f8', ('time', 'level', ))
        iwp_lay_out.units = 'gm-2'
        iwp_lay_out[:] = iwp_lay[:] * 1e3

        lwp_out = f.createVariable('liquid_water_path_MWR', 'f8', ('time', ))
        lwp_out.units = 'gm-2'
        lwp_out.comment = 'This variable is the vertically integrated liquid water directly over the site. The temporal correlation of errors in liquid water path means that it is not really meaningful to distinguish bias from random error, so only an error variable is provided. Original comment: This value has been subtracted from the original clwvi (only zenith!) value to account for instrument calibration drifts. The information is designated for expert user use.'
        lwp_out[:] = lwp[:]*1e3

        lwp_err_out = f.createVariable('liquid_water_path_error_MWR', 'f8', ('time', ))
        lwp_err_out.units = 'gm-2'
        lwp_err_out.comment = 'This variable is a rough estimate of the one-standard-deviation error in liquid water path, calculated as a combination of a 20 g m-2 linear error and a 25% fractional error.'
        lwp_err_out[:] = lwp_err[:]*1e3

        iwc_out = f.createVariable('ice_water_content', 'f8', ('time', 'level', ))
        iwc_out.units = 'gm-3'
        iwc_out.comment = 'This variable was calculated from the 35.5-GHz radar reflectivity factor after correction for gaseous attenuation, and temperature taken from a forecast model, using the following empirical formula: log10(iwc[g m-3]) = 0.000242Z[dBZ]T[degC] + 0.0699Z[dBZ] + -0.0186T[degC] + -1.63. In this formula Z is taken to be defined such that all frequencies of radar would measure the same Z in Rayleigh scattering ice. However, the radar is more likely to have been calibrated such that all frequencies would measure the same Z in Rayleigh scattering liquid cloud at 0 degrees C. The measured Z is therefore multiplied by |K(liquid,0degC,35GHz)|^2/0.93 = 0.9441 before applying this formula. The formula has been used where the "categorization" data has diagnosed that the radar echo is due to ice, but note that in some cases supercooled drizzle will erroneously be identified as ice. Missing data indicates either that ice cloud was present but it was only detected by the lidar so its ice water content could not be estimated, or that there was rain below the ice associated with uncertain attenuation of the reflectivities in the ice. Note that where microwave radiometer liquid water path was available it was used to correct the radar for liquid attenuation when liquid cloud occurred below the ice; this is indicated a value of 3 in the iwc_retrieval_status variable.  There is some uncertainty in this prodedure which is reflected by an increase in the associated values in the iwc_error variable. When microwave radiometer data were not available and liquid cloud occurred below the ice, the retrieval was still performed but its reliability is questionable due to the uncorrected liquid water attenuation. This is indicated by a value of 2 in the iwc_retrieval_status variable, and an increase in the value of the iwc_error variable'
        iwc_out[:] = iwc[:]*1e3

        iwc_err_out = f.createVariable('ice_water_content_error', 'f8', ('time', 'level', ))
        iwc_err_out.units = 'dB'
        iwc_err_out.comment = 'This variable is an estimate of the one-standard-deviation random error in ice water content due to both the uncertainty of the retrieval (about +50%/-33%, or 1.7 dB), and the random error in radar reflectivity factor from which ice water content was calculated. When liquid water is present beneath the ice but no microwave radiometer data were available to correct for the associated attenuation, the error also includes a contribution equivalent to approximately 250 g m-2 of liquid water path being uncorrected for. As uncorrected liquid attenuation actually results in a systematic underestimate of ice water content, users may wish to reject affected data; these pixels may be identified by a value of 2 in the iwc_retrieval_status variable. Typical errors in temperature contribute much less to the overall uncertainty in retrieved ice water content so are not considered. Missing data in iwc_error indicates either zero ice water content (for which an error in dB would be meaningless), or no ice water content value being reported. Note that when zero ice water content is reported, it is possible that ice cloud was present but was just not detected by any of the instruments.'
        iwc_err_out[:] = iwc_error[:]
        
        iwc_bias_out = f.createVariable('ice_water_content_bias', 'f8', ('const', ))
        iwc_bias_out.units = 'dB'
        iwc_bias_out.comment = 'This variable is an estimate of the possible systematic error (one-standard-deviation) in ice water content due to the calibration error of the radar reflectivity factor from which it was calculated.'
        iwc_bias_out[:] = iwc_bias

        iwc_st_out = f.createVariable('ice_water_content_status', 'i4', ('time', 'level', ))
        iwc_st_out.comment = 'This variable describes whether a retrieval was performed for each pixel, and its associated quality, in the form of 8 different classes. The classes are defined in the definition and long_definition attributes. The most reliable retrieval is that without any rain or liquid cloud beneath, indicated by the value 1, then the next most reliable is when liquid water attenuation has been corrected using a microwave radiometer, indicated by the value 3, while a value 2 indicates that liquid water cloud was present but microwave radiometer data were not available so no correction was performed. No attempt is made to retrieve ice water content when rain is present below the ice; this is indicated by the value 5.'
        iwc_st_out.definition = '0: No ice present 1: Reliable retrieval 2: Unreliable retrieval due to uncorrected attenuation from liquid water below the ice (no liquid water path measurement available) 3: Retrieval performed but radar corrected for liquid attenuation using radiometer liquid water path which is not always accurate 4: Ice detected only by the lidar 5: Ice detected by radar but rain below so no retrieval performed due to very uncertain attenuation 6: Clear sky above rain, wet-bulb temperature less than 0degC: if rain attenuation were strong then ice could be present but undetected 7: Drizzle or rain that would have been classified as ice if the wet-bulb temperature were less than 0degC: may be ice if temperature is in error'
        iwc_st_out[:] = iwc_st[:]

        reff_out = f.createVariable('reff_Frisch', 'f8', ('time', 'level', ))
        reff_out.units = "um"
        reff_out.comment = 'This variable was calculated for the profiles where the "categorization" data has diagnosed that liquid water is present the cloud droplet effective radius is calculated after Frisch et al (2002), relating Z with r_eff by assuming a lognormal size distribution, its width and the number concentration of the cloud droplets.'
        reff_out[:] = reff[:]*1e6

        reff_err_out = f.createVariable('reff_Frisch_error', 'f8', ('time', 'level', ))
        reff_err_out.units = "um"
        reff_err_out.comment = 'This variable is an estimate of the random error in effective radius assuming an error in Z of ddBZ= 2. in the spectral width dsigma_x = 0.1, and in the LWP Q of 5e-3 kg/m3'
        reff_err_out[:] = reff_error[:]*1e6

        reff_st_out = f.createVariable('reff_Frisch_status', 'i4', ('time', 'level', ))
        reff_st_out.comment = ''
        reff_st_out.definiton = '0: No data: No cloud observed. 1: Reliable retrieval. 2: Mix of drops and ice: Droplets and ice crystals coexist within pixel. Z may be biased by large crystals. 3: Precipitation in profile: Drizzle and rain affects LWP retrieval of MWR but also the target reflectivity. 4: Surrounding ice: Less crucial! Ice crystals in the vicinity of a droplet pixel may also bias its reflectivity.'
        reff_st_out[:] = reff_st[:]

        reff_ice_out = f.createVariable('reff_ice', 'f8', ('time', 'level', ))
        reff_ice_out.units = 'um'
        reff_ice_out.comment = 'This variable was calculated from the 35.5-GHz radar reflectivity factor after correction for gaseous attenuation, and temperature taken from a forecast model, using the following empirical formula: log10($\mathregular{\alpha}$[g m-3]) = -0.000205Z[dBZ]T[degC] + 0.0016Z[dBZ] + -0.0015T[degC] + -1.52. In this formula $\mathregular{\alpha}$ is taken to be defined such that all frequencies of radar would measure the same Z in Rayleigh scattering ice. However, the radar is more likely to have been calibrated such that all frequencies would measure the same Z in Rayleigh scattering liquid cloud at 0 degrees C. The measured Z is therefore multiplied by |K(liquid,0degC,35GHz)|^2/0.93 = 0.9441 before applying this formula. The formula has been used where the "categorization" data has diagnosed that the radar echo is due to ice, but note that in some cases supercooled drizzle will erroneously be identified as ice. Missing data indicates either that ice cloud was present but it was only detected by the lidar so its ice water content could not be estimated, or that there was rain below the ice associated with uncertain attenuation of the reflectivities in the ice. Note that where microwave radiometer liquid water path was available it was used to correct the radar for liquid attenuation when liquid cloud occurred below the ice; this is indicated a value of 3 in the iwc_retrieval_status variable.  There is some uncertainty in this prodedure which is reflected by an increase in the associated values in the iwc_error variable. When microwave radiometer data were not available and liquid cloud occurred below the ice, the retrieval was still performed but its reliability is questionable due to the uncorrected liquid water attenuation. This is indicated by a value of 2 in the iwc_retrieval_status variable, and an increase in the value of the iwc_error variable'
        reff_ice_out[:] = reff_ice[:]

        reff_ice_err_out = f.createVariable('reff_ice_error', 'f8', ('time', 'level', ))
        reff_ice_err_out.units = 'um'
        reff_ice_err_out.comment = 'Error in effective radius of ice particles due to error propagation, of r_e = 3/(2 rho_i) IWC / alpha, using error for IWC and alpha as given in Hogan 2006.'
        reff_ice_err_out[:] = reff_ice_error[:]

        reff_ice_st_out = f.createVariable('reff_ice_status', 'i4', ('time', 'level', ))
        reff_ice_st_out.comment = 'This variable describes whether a retrieval was performed for each pixel, and its associated quality, in the form of 8 different classes. The classes are defined in the definition and long_definition attributes. The most reliable retrieval is that without any rain or liquid cloud beneath, indicated by the value 1, then the next most reliable is when liquid water attenuation has been corrected using a microwave radiometer, indicated by the value 3, while a value 2 indicates that liquid water cloud was present but microwave radiometer data were not available so no correction was performed. No attempt is made to retrieve ice water content when rain is present below the ice; this is indicated by the value 5.'
        reff_ice_st_out.definition = '0: No ice present 1: Reliable retrieval 2: Unreliable retrieval due to uncorrected attenuation from liquid water below the ice (no liquid water path measurement available) 3: Retrieval performed but radar corrected for liquid attenuation using radiometer liquid water path which is not always accurate 4: Ice detected only by the lidar 5: Ice detected by radar but rain below so no retrieval performed due to very uncertain attenuation 6: Clear sky above rain, wet-bulb temperature less than 0degC: if rain attenuation were strong then ice could be present but undetected 7: Drizzle or rain that would have been classified as ice if the wet-bulb temperature were less than 0degC: may be ice if temperature is in error'
        reff_ice_st_out[:] = reff_ice_st[:]
        
if __name__ == '__main__':
    for month in [5,6,7]:
        for day in range(32):
            try:
                main(month, day)
            except Exception:
                continue
