import datetime
import glob
import os
import re
import processing
from qgis.core import *

# USER_SETTING_1   Old data
prev_data_path = r'D:\wrk_TORIS\Source_geo_data\test\Oct'

# USER_SETTING_2   New data
new_data_path = r'D:\wrk_TORIS\Source_geo_data\test\Nov '

convert_2_gdb = True
crs = 'USER:100022'
'''
Инструмент сравнивает два набора TAB файлов;
На вход принимает от пользователя два пути в папкам: со старыми табами, и с новыми (# USER_SETTING_1 и # USER_SETTING_2  );
- Анализирует набор файлов по сосотаву и названиям;
- Анализирует изменения геометрии объектов;
- Анализирует изменения в атрибутах объектов;
- Учитывает то, что таб может содержать разные типы геометрии, в том числе объекты без геометрии;
- Исходные файлы не меняет;
- При анализе очередного слоя спрашивает у пользователя, какие геометрии брать; Таким образом, можно не обрабатывать заведомо неиспользуемые объекты;
- Преполагается, что при загрузке у пользователя выключена галочка "Добавить слои в группу". Если галочка будет стоять, то слои не будут проанализированы;
  Эту возможность можно использовать, чтобы исключить те или иные слои из обработки;
- Результат анализа сохраняет в файл _Comparation.txt в папке с новыми данными;
- Обновлённые объекты сохраняет в файлы *_added.gpkg   *_deleted.gpkg;
- Внимание! Изменённые объекты попадают в оба файла одновременно: и в удалённые, и в добавленные. Надо будет подумать как их лучше фильтровать;
- Можно сравнивать не только данные от КИО, но и любые другие наботы таб-файлов;
- Время обработки для 45 слоёв около 45 минут;


Инструмент запускается из-под QGIS, в консоли Python

'''
def print_log(mes):
    print(mes)
    log.write(mes)

def compare_tabs(field_names_old, field_names_new, basename):
    if field_names_old != field_names_new:
        mes = f'\n!!!!!!!!!!WARNING!!!!!!!!!\nНабор атрибутов слоя {basename} отличается!'
        print_log(mes)
        
        for field in field_names_old:
            if field not in field_names_new:
                mes = f'\nПоле {field} есть в предыдущем наборе, но нет в новом'
                print_log(mes)
                
        for field in field_names_new:
            if field not in field_names_old:
                mes = f'\nПоле {field} есть в новом наборе, но нет в предыдущем'
                print_log(mes)
        
        return True

    else:
        return False


def compare_data(fc, old_fc, type_geom):
    basename = fc.split(' ')[-1]
    
    fc_lyr = QgsVectorLayer(fc)
    old_fc_lyr = QgsVectorLayer(old_fc)

    
    field_names = [field.name() for field in old_fc_lyr.fields()]
    field_names_new = [field.name() for field in fc_lyr.fields()]
    if compare_tabs(field_names, field_names_new, basename) is True:
        print(f'\n!!!!!!!!!!WARNING!!!!!!!!!\nНабор атрибутов слоя {basename} отличается!')
    
    res = processing.run("native:detectvectorchanges", 
                        {'ORIGINAL':QgsProcessingFeatureSourceDefinition(old_fc, 
                                selectedFeaturesOnly=False, 
                                featureLimit=-1, 
                                flags=QgsProcessingFeatureSourceDefinition.FlagOverrideDefaultGeometryCheck, 
                                geometryCheck=QgsFeatureRequest.GeometrySkipInvalid
                                ),
                        'REVISED':QgsProcessingFeatureSourceDefinition(fc, 
                                                                        selectedFeaturesOnly=False, 
                                                                        featureLimit=-1, 
                                                                        flags=QgsProcessingFeatureSourceDefinition.FlagOverrideDefaultGeometryCheck, 
                                                                        geometryCheck=QgsFeatureRequest.GeometrySkipInvalid
                                                                        ),
                        'COMPARE_ATTRIBUTES':field_names,

                        'MATCH_TYPE':1,
                        'UNCHANGED':'TEMPORARY_OUTPUT',
                        'ADDED':basename+'_added.gpkg',
                        'DELETED':basename+'_deleted.gpkg'})
    
    del res
    fc_count = QgsVectorLayer(basename+'_added.gpkg')
    feats_count = fc_count.featureCount()
    if feats_count == 0:   
        del fc_count
        del feats_count
        os.remove(basename+'_added.gpkg')
    else:
        mes = f'\nВ слое {basename} добавлено {feats_count} объектов'
        print_log(mes)
    
    fc_count = QgsVectorLayer(basename+'_deleted.gpkg')
    feats_count = fc_count.featureCount()
    if feats_count == 0:   
        del fc_count
        del feats_count    
        os.remove(basename+'_deleted.gpkg')
    else:
        mes = f'\nВ слое {basename} удалено {feats_count} объектов'
        print_log(mes)
    
def convert2gdb(fc, crs, type_geom, basename):
    res1 = processing.run("native:assignprojection", 
                            {
                            'INPUT':fc,
                            'CRS':QgsCoordinateReferenceSystem(crs),
                            'OUTPUT':'TEMPORARY_OUTPUT'
                            })
    res2 = processing.run("native:fixgeometries", 
                {
                'INPUT':res1['OUTPUT'],
                'METHOD':1,
                'OUTPUT':basename+'_'+ type_geom_dict[type_geom]+'_fxd.gpkg'
                })
    res3 = processing.run("gdal:convertformat", 
                {
                'INPUT':basename+'_'+ type_geom_dict[type_geom]+'_fxd.gpkg',
                'CONVERT_ALL_LAYERS':False,
                'OPTIONS':'',
                'OUTPUT':'data_new.gdb'
                })                
    return True

    
os.chdir(prev_data_path)
old_tab_files={key: os.path.abspath(key) for key in glob.glob('*.tab')}

os.chdir(new_data_path)
new_tab_files={key: os.path.abspath(key) for key in glob.glob('*.tab')}

log_file = '_Comparation.log'
log = open(log_file, 'a')
log.write('\n=========================================================================================\n')
log.write(str(datetime.datetime.now()))

mes = '\n===== СРАВНЕНИЕ НАБОРА ФАЙЛОВ ====='
print_log(mes)
mes = '\nНовые данные:'
print_log(mes)
mes = str('\n'+new_data_path)
print_log(mes)
mes = '\nСтарые данные:'
print_log(mes)
mes = str('\n'+prev_data_path)
print_log(mes)

count = 0
for key in new_tab_files:
    if key not in old_tab_files:
        mes = f'\n!!!!! Слой {key} отсутствует в предыдущем наборе файлов'
        print_log(mes)
        count += 1
        
for key in old_tab_files:
    if key not in new_tab_files:
        mes = f'\n!!!!! Слой {key} отсутствует в новом наборе файлов. Был в предыдущем'
        print_log(mes)
        count += 1
        
mes = str(f'\nВсего в новом наборе {len(new_tab_files)} слоёв.\nВ предыдущем наборе {len(old_tab_files)} слоёв')
print_log(mes)
mes = str(f'\nНайдено {count} различий по составу файлов')
print_log(mes)
log.close()


log = open(log_file, 'a')    
mes = '\n\n== СРАВНЕНИЕ ГЕОМЕТРИЙ И АТРИБУТОВ СЛОЁВ =='
print_log(mes)
log.close()


unusefull_lst = []
type_geom_dict = {
                0: 'point',
                1: 'line',
                2: 'polygon',
                3: 'without_geometry',
                4: 'table',
                5: 'unknown_5'
                }
                
for fc in new_tab_files:
    log = open(log_file, 'a')
    mes = f'\n\n{fc}'
    print_log(mes)
    
    basename = str(fc[:-4])
    layer_new = iface.addVectorLayer(fc, 'new_data', "ogr")
    if fc in old_tab_files:
        layer_old = iface.addVectorLayer(old_tab_files[fc], 'old_data', "ogr")
        datas_lst = QgsProject.instance().mapLayers().values()
        for layer in datas_lst:
            if re.findall('new_data', layer.name()):
                type_geom = layer.geometryType()
                layer.setName(layer.name()+'_'+type_geom_dict[type_geom])
                new_data = layer.name()

                for lyr in datas_lst:
                    if re.findall('old_data', lyr.name()) and lyr.geometryType() == type_geom:
                        lyr.setName(lyr.name()+'_'+type_geom_dict[type_geom])
                        old_data = lyr.name()
                
                if convert_2_gdb is True:
                    convert2gdb(new_data, crs, type_geom, basename)
                
                compare_data(new_data, old_data, type_geom_dict[type_geom])

            
        for layer in QgsProject.instance().mapLayers().values():
            QgsProject.instance().removeMapLayers( [layer.id()] )    

    log.close()
print(f'Результаты сравнения в файле {new_data_path}\\{log_file}')
print('Finish')