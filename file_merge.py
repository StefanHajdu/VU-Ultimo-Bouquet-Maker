import os
import glob

def bouquet_merge(path):
    first_file = os.listdir(path)[0]
    while first_file:
        file_lang = first_file.split('_')[1]
        same_lang_files = glob.glob(path + '/*' + file_lang)
        merged_file_name = '/home/stephenx/Dokumenty/python/Ultimo_Bouqeting/bouquets/Channels_' + file_lang.upper()
        merged_file = open(merged_file_name, 'w')

        for file in same_lang_files:
            file_read = open(file, 'r')
            contents = file_read.read()
            merged_file.write(contents)
            file_read.close()
            os.remove(file)

        same_lang_files.clear()
        try:
            first_file = os.listdir(path)[0]
        except IndexError:
            print("Bouquets were merged by language.")
            break
