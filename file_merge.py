import os
import glob

def audio_merge(path, args):
    first_file = os.listdir(path)[0]
    while first_file:
        file_lang = first_file.split('_')[1]
        same_lang_files = glob.glob(path + '/*' + file_lang)
        if args.tv_based:
            name = file_lang.split('.')[0].upper() + ' (TV)'
            merged_file_name = 'bouquets/userbouquet.' + 'mybouquet_' + file_lang.lower()
        else:
            name = file_lang.split('.')[0].upper() + ' (RADIO)'
            merged_file_name = 'bouquets/userbouquet.' + 'mybouquet_' + file_lang.lower()

        merged_file = open(merged_file_name, 'w')
        merged_file.write(f"#NAME {name}\n")

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

def merge():
    user_input = str(input("Type bouquet name (with prefered suffix .tv/.radio !!!): "))
    #print(user_input.split('.')[1])
    if user_input.split('.')[1] == 'radio' or user_input.split('.')[1] == 'tv':
        file_name = 'bouquets/userbouquet.' + user_input
        merged_file = open(file_name, 'w')
        merged_file.write(f"#NAME {user_input.split('.')[0]}\n")

        bouquet_files = os.listdir('bouquets')
        for file in bouquet_files:
            if file == 'userbouquet.' + user_input:
                continue
            file_read = open('bouquets/' + file, 'r')
            contents = file_read.readlines()[1:]
            merged_file.writelines(contents)
            file_read.close()
            # os.remove('bouquets/' + file)
    else:
        print("INPUT ERROR: Invalid input.")
        exit()

    print(f"Bouquets were merged. New bouquet {'userbouquet.' + user_input} was created")
