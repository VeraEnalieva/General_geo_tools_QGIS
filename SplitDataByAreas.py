# ЗАДАЧА. Нарезать данные по регионам
# ЧТО разрезаем - загрузить в проект. Это должны быть однотипные данные. 
# Например, только зелень, только здания. Чтобы данные в итоговых файлах не перемешались по смыслу
# ЧЕМ режем - укажите в USER_SETTINGS_1. Это должен быть один полигональный слой, у которого в одном из атрибутов указаны уникальные названия регионов.
# Например, если разрезаем по районам города, то в поле NAME должно быть: Адмиралтейский, Петроградский и т.д.
# Если разрезаем по островкам, то в поле ISLAND должен быть уникальный номер островка.
# Название поля укажите в параметре USER_SETTINGS_2
# КУДА сохранить нарезанные данные укажите в параметре USER_SETTINGS_3
# Готовые файлы будут деэать в этой папке с поcтфиксом _data

import glob
import os

#USER_SETTINGS_1   Путь к файлу с полигонами нарезки
areas_path = r'D:\wrk_TORIS\Source_geo_data\ИАЦ_2024_01_31\all_twn\Done\D_ADM.tab'

#USER_SETTINGS_2   Поле с уникальными названиями регионов
areas_names_field = 'Name'

#USER_SETTINGS_3   Папка, куда сложить результат
result_path = r'D:\temp'

#USER_SETTINGS_3   Расширение для выходных файлов  gpkg, shp,
ext='gpkg'  

os.chdir(result_path)


def crop_by_mask(mask, fc):
    
    out_name = fc+'_'+mask
    res = processing.run("gdal:clipvectorbypolygon", 
        {
        'INPUT':QgsProcessingFeatureSourceDefinition(fc, selectedFeaturesOnly=False, featureLimit=-1, flags=QgsProcessingFeatureSourceDefinition.FlagOverrideDefaultGeometryCheck, geometryCheck=QgsFeatureRequest.GeometrySkipInvalid),
        'MASK':QgsProcessingFeatureSourceDefinition(mask, selectedFeaturesOnly=False, featureLimit=-1, flags=QgsProcessingFeatureSourceDefinition.FlagOverrideDefaultGeometryCheck, geometryCheck=QgsFeatureRequest.GeometrySkipInvalid),
        'OPTIONS':'',
        #'OUTPUT':out_name
        'OUTPUT':'TEMPORARY_OUTPUT'
        })
    #return os.path.abspath(res['OUTPUT'])
    return res['OUTPUT']


def merge_news(file_lst):
    new_region_file = (os.path.basename(one_part)).split('.')[0]+'_data.'+ext
    merged_file = processing.run("native:mergevectorlayers", 
        {
        'LAYERS': file_lst,
        'CRS': '',
        'OUTPUT': new_region_file
        })
    del file_lst
    
    return merged_file

# Создаём отдельные файлы для каждого из районов. 1 район = 1 файл
processing.run("native:splitvectorlayer", 
    {
    'INPUT':QgsProcessingFeatureSourceDefinition(areas_path, selectedFeaturesOnly=False, featureLimit=-1, flags=QgsProcessingFeatureSourceDefinition.FlagOverrideDefaultGeometryCheck, geometryCheck=QgsFeatureRequest.GeometrySkipInvalid),
    'FIELD': areas_names_field,
    'PREFIX_FIELD':False,
    'FILE_TYPE':0,
    'OUTPUT':result_path
    })

split_parts_files = glob.glob('*.gpkg')

datas_lst = QgsProject.instance().mapLayers().values()
files2del=[]
for one_part in split_parts_files:
    print(one_part)
    files2merge=[]

    for fc in datas_lst:
        cropped_file = crop_by_mask(one_part, fc.name())
        feats_count = QgsVectorLayer(cropped_file).featureCount()
        if feats_count > 0:
            files2merge.append(cropped_file)

        del cropped_file
    
    if len(files2merge) > 0:
        merge_news(files2merge)
        files2del.extend(files2merge)
    
    os.remove(one_part)
    del files2merge
    
        
print('Finish')    