## Software

It is recommended to use [Anaconda](https://www.anaconda.com/products/individual), which contains the Python interpreter and the Jupyter Notebooks. 

## Download Cloudnet data

Cloudnet data is stored on www.pangaea.de. One needs to run get_cloudnet/download_data.py to download data for LWC, LWP, IWC, reff_Frisch and reff_ice. get_cloudnet/merge_data.py reads the data from the downloaded netCDF files and merges all data of one day into one file.

## Compare results

Go to compare_TCWret_and_Cloudnet and run the Jupyter-notebooks. Here you can find notebooks comparing LWP, IWP, rliq and rice. Each notebook contains some code to download TCWret data from [Pangaea](https://doi.pangaea.de/10.1594/PANGAEA.933829). The analysis of different ice crystal shapes is performed using the notebook in compare_different_ice_shapes. Data of different ice crystal shapes is stored in data_TCWret.