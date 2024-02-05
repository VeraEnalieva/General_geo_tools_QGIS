import glob
import os
import processing

# USER_SETTING_1  Path to SID files
os.chdir(r'D:\wrk_ecopassport\ortho\2008\final_test')


f_lst = [f for f in glob.glob('*.sid')]

for file in f_lst:
    print(file)
    processing.run("gdal:translate", 
            {
            'INPUT':file,
            #'TARGET_CRS':QgsCoordinateReferenceSystem('USER:100026'),
            'TARGET_CRS':None,
            'NODATA':None,
            'COPY_SUBDATASETS':False,
            'OPTIONS':'',
            'EXTRA':'',
            'DATA_TYPE':0,
            'OUTPUT':file[:-4]+'.jpg'
            }
            )
            
print('Finish')            