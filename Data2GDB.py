# 2023_04_12
# Все данные, которые загружены в проект:
# - добавляет к названию слоя постфикс point, area, line, noGeometry
# - присваивает проектцию МСК-64. Предполагается, что все исходные имеено в ней. 
#   Если не так, то в my_crs.createFromProj4 надо переписать другую
# - конвертирует все гео слои в gpkg
# - объединяет все гео слои в единый gpkg
# - конвертирует все гео слои с один GDB
# Пользовательская настройка одна - os.chdir - путь к выходным файлам


from qgis.core import QgsProject
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsCoordinateReferenceSystem
import os
import datetime

# USER setting 1. Укажите  папку, в которую сохранять итоговые файлы
os.chdir(r'D:\wrk_genplan\Data_2023')
#names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
#for n in names[:3]:
#    print(n)
count_total = 0
count_geom = 0
# crs_wkt = 'PROJCS["MSK_Leningrad_1964",GEOGCS["GCS_Pulkovo_1942",DATUM["D_Pulkovo_1942",SPHEROID["Krasovsky_1940",6378245.0,298.3],TOWGS84[25,-141,-78.5,0,0.35,0.736,0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",95942.16999],PARAMETER["False_Northing",-6552810.0],PARAMETER["Central_Meridian",30.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'

my_crs = QgsCoordinateReferenceSystem("USER:100026")
# my_crs = QgsCoordinateReferenceSystem("USER:100022")
#my_crs.createFromProj4('+proj=tmerc +lat_0=0 +lon_0=43.05 +k=1 +x_0=1300000 +y_0=-5214743.504 +ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs')
#my_crs.saveAsUserCrs("MSK64_Len2023")

list_layers = []
for vLayer in QgsProject.instance().mapLayers().values():
    print(vLayer.name())
    geom_type = vLayer.geometryType()
    count_total +=1
    
    if geom_type == 0: # point
        vLayer.setName(vLayer.name()+'_point')
        count_geom += 1
    elif geom_type == 1: # line
        vLayer.setName(vLayer.name()+'_line')
        count_geom += 1
    elif geom_type == 2: # area
        vLayer.setName(vLayer.name()+'_polygon')
        count_geom += 1
    else:
        vLayer.setName(vLayer.name()+'_no_Geometry')
        continue
    

    # vLayer.setCrs(QgsCoordinateReferenceSystem(3857, QgsCoordinateReferenceSystem.EpsgCrsId))
    vLayer.setCrs(QgsCoordinateReferenceSystem(my_crs))

    fixed_geom = processing.run("native:fixgeometries", 
                {'INPUT':vLayer,
                'METHOD':1,
                'OUTPUT':'TEMPORARY_OUTPUT'
                })
    #QgsVectorFileWriter.writeAsVectorFormat(vLayer, vLayer.name(), "UTF-8", vLayer.crs(), "ESRI Shapefile")
    res = QgsVectorFileWriter.writeAsVectorFormat(fixed_geom['OUTPUT'], vLayer.name(), "UTF-8",vLayer.crs(),"GPKG")
    out_file  = str(vLayer.name())+'.gpkg'
    print(out_file)
    #list_layers.append(vLayer)
    list_layers.append(out_file)

print (f'Итого таблиц данных: {count_total}\nВ том числе с валидной геометрией:{count_geom}')
print('Объединение gpkg')
processing.run("native:package", {'LAYERS': list_layers,
								'OUTPUT':'_Merged_Package.gpkg',
								'OVERWRITE':False,
								'SAVE_STYLES':True,
								'SAVE_METADATA':True,
								'SELECTED_FEATURES_ONLY':False,
								'EXPORT_RELATED_LAYERS':False})

print('Формирование GDB')
today = f"{datetime.datetime.now():%Y_%m_%d}"
processing.run("gdal:convertformat", {'INPUT':'_Merged_Package.gpkg',
                                    'CONVERT_ALL_LAYERS':True,
                                    'OPTIONS':'',
                                    'OUTPUT':'Package_'+today+'.gdb'})

print('Завершено')
