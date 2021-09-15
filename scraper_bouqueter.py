import requests
import time
import csv
import re
import argparse
from bs4 import BeautifulSoup
import file_merge

def prepare_column_names(html_names):
    names = []
    for name in html_names:
        # parse channel's name
        try:
            channel_name = name.a.text
        except:
            try:
                channel_name = name.i.text
            except:
                try:
                    channel_name = name.text.strip()
                except:
                    channel_name = "no information"

        if channel_name == "Name":
            continue
        else:
            names.append(channel_name)
    return names

# prepare SID, Country, Category
def prepare_column_same(html_list, word):
    list = []
    for item in html_list:
        if len(item) == 0:
            list.append("no information")
        elif item.text == word:
            continue
        else:
            list.append(item.text)
    return list

# prepare Audio
def prepare_column_audio(html_audios, word):
    list = []
    for item in html_audios:
        langs_string = ""
        languages = item.find_all("font", color="blue")
        if len(languages) == 0:
            list.append("no information")
            continue
        else:
            for lang in languages:
                langs_string = langs_string + lang.text + ','
            list.append(langs_string)
    return list

# get TID and NID for collenction of channels in table
def get_tranponder_ids(html_frq_table):
    #ids = html_frq_table.find_all("td", width="4%")
    #return ids[1].text, ids[0].text

    fqr_row = html_frq_table.find("tr")
    tid = fqr_row.find_all('td')[-2]
    nid = fqr_row.find_all('td')[-3]
    return tid.text, nid.text

def get_satellite_pos(html_frq_table):
    fqr_row = html_frq_table.find("tr")
    pos = fqr_row.find_all('td')[0]
    return pos.text

def scrape_and_write(soup):
    # find tables that contain channel elements
    html_tables = soup.find_all("table", class_="fl")
    for table in html_tables:

        html_frq_table = table.find_previous("table", class_="frq")
        tid, nid = get_tranponder_ids(html_frq_table)
        pos = get_satellite_pos(html_frq_table)

        # find channel names
        html_names = table.find_all("td", class_="ch")
        # empty table are not interesting
        if not html_names:
            continue
        # find channel countries
        html_countries = table.find_all("td", class_="w3-hide-small pays")
        # find channel category
        html_categories = table.find_all("td", class_="w3-hide-small genre")
        # find channel audio
        html_audios = table.find_all("td", width="8%")
        # find SID
        html_sid = table.find_all("td", {'class':['s', 'ns']})

        # prepare lists for .csv file
        names = prepare_column_names(html_names)
        sid = prepare_column_same(html_sid, "SID")
        countries = prepare_column_same(html_countries, "Country")
        categories = prepare_column_same(html_categories, "Category")
        audios = prepare_column_audio(html_audios, "Audio")

        # write to .csv file by columns
        # open .csv file
        with open("channels.csv", "a") as channels_csv:
            csv_writer = csv.writer(channels_csv, delimiter=';')
            for item in range(len(names)):
                csv_writer.writerow([sid[item], int(float(pos[:-2])*10), tid, nid, names[item], countries[item], categories[item], audios[item]])

def prepare_url_pos(pos):
    char_to_replace = {',': '.', '°': ''}
    for key, value in char_to_replace.items():
        pos = pos.replace(key, value)
    return pos

def scrap(url):
    try:
        html_text = requests.get(url).text
        # Prepare the soup
        soup = BeautifulSoup(html_text, "html.parser")
        print(f"Now Scraping - {url}")
        scrape_and_write(soup)
        time.sleep(2)
    except Exception as e:
        return e

def browse_and_scrape(main_url, command):
    if command.frequency:
        list_of_satellites = find_orbital_pos(satellites_xml)
        print(list_of_satellites)
        for satellite in list_of_satellites:
            # prepare url for scraping
            formated_sat = prepare_url_pos(satellite)
            url = main_url + "pos-" + formated_sat + ".php"
            excp = scrap(url)
            if excp:
                return excp

    if command.packages:
        package_list = parse_config_file("-PACKAGES")
        print("Choose from packages you wish to create bouquets from.")
        print("Available packages:")
        counter = 1
        for pack in package_list:
            print(f"{counter}. {pack.split(',')[0]}")
            counter += 1
        print("\nWrite index numbers separated by ','. To select all press Enter.")
        choosen = str(input("Select: "))
        print('\n')
        if not choosen:
            for package in package_list:
                url = package.split(',')[1]
                excp = scrap(url)
                if excp:
                    return excp
        else:
            pack_incides = choosen.split(',')
            for index in pack_incides:
                if int(index)-1 >= counter or int(index) == 0:
                    print("INPUT ERROR: Invalid input.")
                    exit()
                url = package_list[int(index)-1].split(',')[1]
                excp = scrap(url)
                if excp:
                    return excp

# find all orbital possitions available in file satellites.xml
def find_orbital_pos(satellites_xml_path):
    # orbitals decimal separator are written like 1.0 in .xml so we scrap them directly
    list_of_obital_pos = ["0.8W", "0.6W"]

    infile = open(satellites_xml_path, "r", encoding="ISO-8859-1")
    content = infile.read()
    print("File satellites.xml found and loaded.")
    soup = BeautifulSoup(content, 'lxml')

    satellites = soup.find_all("sat")
    for satellite in satellites:
        name = satellite["name"]
        list_of_obital_pos.append(name.split()[0])
    return list_of_obital_pos

class Channel:
    def __init__(self, sid, pos, tid, nid, name, country, category, languages):
        self.sid = sid
        self.pos = pos
        self.tid = tid
        self.nid = nid
        self.name = name
        self.country = country
        self.category = category
        self.language = languages

    def __str__(self):
        return f"SID = {self.sid}; POS = {self.pos}; TID = {self.tid}; NID = {self.nid}; Name = {self.name}; Country = {self.country}; Category = {self.category}; Languages = {self.language}"

def calc_dict_key_encode(channel):
    return channel.sid + channel.pos + channel.tid + channel.nid

def create_channel_dict(filename):
    channel_dict = {}
    with open(filename) as channels_csv:
        csv_reader = csv.reader(channels_csv, delimiter=';')
        next(csv_reader)
        for row in csv_reader:
            # 0 -> SID
            # 1 -> POS
            # 2 -> TID
            # 3 -> NID
            # 4 -> Name
            # 5 -> Country
            # 6 -> Category
            # 7 -> Languages
            channel = Channel(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
            channel_dict[calc_dict_key_encode(channel)] = channel
    return channel_dict

def calc_dict_key_decode(sid, pos, tid, nid):
    return str(sid) + str(pos) + str(tid) + str(nid)

def parse_config_file(tag):
    custom_pref = []
    preference_active = False
    try:
        with open("config", "r") as config_file:
            for line in config_file:
                if line.startswith('#'):
                    preference_active = False
                    continue
                if preference_active:
                    # prefs = line.split('/')
                    # custom_categories.append(prefs[0])
                    # custom_langs.append(prefs[1])
                    if tag == '-SATELLITESXML' or tag == '-LAMEDB5':
                        custom_pref.append(line[:-1])
                    else:
                        custom_pref.append(line[:-1].lower())
                if line.startswith(tag):
                    preference_active = True
    except FileNotFoundError:
        print("ERROR: No configuration file.")
        exit()

    return custom_pref

def channel_in_prefs(custom_prefs, channel, command):
    for pref in custom_prefs:
        if command.tv_based:
            if channel.category.lower() in pref and pref.split('/')[1] in channel.language:
                return pref
        if command.radio_based:
            if pref.split('/')[1] in channel.language:
                return pref
    return "not found"

TV = [1, 34, 37]
RADIO = 2

def create_bouquets(channel_dict, lamedb5, command):
    custom_pref = []
    if command.custom_based:
        custom_pref = parse_config_file("-PREFERENCES")

    bouquets_created = []
    all_channels = 0
    matched_channels = 0
    with open(lamedb5) as lamedb5_csv:
        csv_reader = csv.reader(lamedb5_csv, delimiter=':')
        for row in csv_reader:
            # LAMEDB column 0; s => service
            if row[0] == 's':
                all_channels += 1
                # LAMEDB column 1; sid => service_id
                l_sid = int(row[1], 16)
                # LAMEDB column 2; transponder => dvb_namespace
                l_transponder = row[2][:4]
                if re.search("^0e0", l_transponder):
                    l_transponder = int(l_transponder[2:], 16)
                else:
                    l_transponder = int(l_transponder, 16)

                l_tid = int(row[3], 16)
                # LAMEDB column 4; nid => original_network_id
                l_nid = int(row[4], 16)

                # LAMEDB column 5; st => service_type
                service_type = int(row[5], 16)

                channel_dict_key = calc_dict_key_decode(l_sid, l_transponder, l_tid, l_nid)
                try:
                    channel = channel_dict[channel_dict_key]
                    matched_channels += 1
                    if command.custom_based:
                        pref = channel_in_prefs(custom_pref, channel, command)
                        if not pref == "not found":
                            if command.radio_based:
                                if service_type == RADIO:
                                    write_to_bouquet_custom(row, channel.name, channel.category, pref.split('/')[1], bouquets_created, command, "RADIO")
                            if command.tv_based:
                                if service_type in TV:
                                    write_to_bouquet_custom(row, channel.name, channel.category, pref.split('/')[1], bouquets_created, command, "TV")
                        else:
                            continue
                    else:
                        if command.radio_based:
                            if service_type == RADIO:
                                write_to_bouquet(row, channel.name, channel.category, channel.language, bouquets_created, command, "RADIO")
                            else:
                                continue
                        if command.tv_based:
                            if service_type in TV:
                                write_to_bouquet(row, channel.name, channel.category, channel.language, bouquets_created, command, "TV")
                            else:
                                continue
                except KeyError:
                    continue

        print(f"{all_channels} channels found in lamedb5.")
        print(f"{matched_channels} channels stored in bouqets.")
        print(f"{all_channels - matched_channels} channels cannot be stored in bouquet.")

        if command.audio_based:
            file_merge.audio_merge('bouquets_tmp', command)

        if command.merge:
            file_merge.merge()

def parse_languages(ch_languages):
    languages = ch_languages.split(",")
    del languages[-1]
    return languages

def num_to_bouquet(strr):
    modified = strr.lstrip('0')
    return modified.upper()

def hexa_to_bouquet(int_str):
    intt = int(int_str)
    hexaa = hex(intt)
    hexa_str = str(hexaa)
    return hexa_str[2:].upper()

DESCRIPTION_COUNT = 0

def write_to_bouquet_custom(lamedb_row, ch_name, ch_category, ch_language, bouquets_created, command, service_type):
    store_path = 'bouquets/'
    # LAMEDB column 5; st => service_type
    st = lamedb_row[5]
    if command.tv_based:
        bouquet = "userbouquet." + ch_category + '_' + ch_language + ".tv"
        tag = ch_category + '_' + ch_language
        name = ch_category + ' ' + ch_language + ' (TV)'
    if command.radio_based:
        bouquet = "userbouquet." + service_type + '_' + ch_language + ".radio"
        tag = ch_category + '_' + ch_language
        name = service_type + ' ' + ch_language + ' (RADIO)'
    if bouquet in bouquets_created:
        bouquet_file = store_path + bouquet
        with open(bouquet_file, 'a') as current_bouquet:
            current_bouquet.write("#SERVICE "+"1:0:"+hexa_to_bouquet(st)+":"+num_to_bouquet(lamedb_row[1])+":"+num_to_bouquet(lamedb_row[3])+":"+num_to_bouquet(lamedb_row[4])+":"+num_to_bouquet(lamedb_row[2])+":0:0:0:"+"\n")
    else:
        bouquets_created.append(bouquet)
        bouquet_file = store_path + bouquet
        with open(bouquet_file, 'w') as current_bouquet:
            global DESCRIPTION_COUNT
            DESCRIPTION_COUNT += 1
            current_bouquet.write(f"#NAME {name.upper()}\n")
            current_bouquet.write("#SERVICE 1:64:" + hexa_to_bouquet(DESCRIPTION_COUNT) + ":0:0:0:0:0:0:0::" + "<====== " + tag + " ======>" + "\n")
            current_bouquet.write("#DESCRIPTION " + "<====== " + tag + " ======>" + "\n")
            current_bouquet.write("#SERVICE "+"1:0:"+hexa_to_bouquet(st)+":"+num_to_bouquet(lamedb_row[1])+":"+num_to_bouquet(lamedb_row[3])+":"+num_to_bouquet(lamedb_row[4])+":"+num_to_bouquet(lamedb_row[2])+":0:0:0:"+"\n")

def write_to_bouquet(lamedb_row, ch_name, ch_category, ch_languages, bouquets_created, command, service_type):
    store_path = ""
    bouquet = ""
    if command.audio_based:
        store_path = 'bouquets_tmp/'
    else:
        store_path = 'bouquets/'
    # LAMEDB column 5; st => service_type
    st = lamedb_row[5]
    languages = parse_languages(ch_languages)
    # to get rid of duplicates in list, we use set (data structure that cannot contain duplicates)
    languages = list(set(languages))
    for lang in languages:
        if command.tv_based:
            bouquet = "userbouquet." + ch_category + '_' + lang + ".tv"
            tag = ch_category + '_' + lang
            name = ch_category + ' ' + lang + ' (TV)'
        if command.radio_based:
            bouquet = "userbouquet." + service_type + '_' + lang + ".radio"
            tag = service_type + '_' + lang
            name = ch_category + ' ' + lang + ' (RADIO)'

        if bouquet in bouquets_created:
            bouquet_file = store_path + bouquet
            with open(bouquet_file, 'a') as current_bouquet:
                if len(bouquets_created) > 1:
                    current_bouquet.write("#SERVICE "+"1:0:"+hexa_to_bouquet(st)+":"+num_to_bouquet(lamedb_row[1])+":"+num_to_bouquet(lamedb_row[3])+":"+num_to_bouquet(lamedb_row[4])+":"+num_to_bouquet(lamedb_row[2])+":0:0:0:"+"\n")
        else:
            bouquets_created.append(bouquet)
            bouquet_file = store_path + bouquet
            with open(bouquet_file, 'w') as current_bouquet:
                global DESCRIPTION_COUNT
                DESCRIPTION_COUNT += 1
                if command.audio_based:
                    current_bouquet.write("#SERVICE 1:64:" + hexa_to_bouquet(DESCRIPTION_COUNT) + ":0:0:0:0:0:0:0::" + "<====== " + tag + " ======>" + "\n")
                    current_bouquet.write("#DESCRIPTION " + "<====== " + tag + " ======>" + "\n")
                    current_bouquet.write("#SERVICE "+"1:0:"+hexa_to_bouquet(st)+":"+num_to_bouquet(lamedb_row[1])+":"+num_to_bouquet(lamedb_row[3])+":"+num_to_bouquet(lamedb_row[4])+":"+num_to_bouquet(lamedb_row[2])+":0:0:0:"+"\n")
                else:
                    current_bouquet.write(f"#NAME {name.upper()}\n")
                    current_bouquet.write("#SERVICE 1:64:" + hexa_to_bouquet(DESCRIPTION_COUNT) + ":0:0:0:0:0:0:0::" + "<====== " + tag + " ======>" + "\n")
                    current_bouquet.write("#DESCRIPTION " + "<====== " + tag + " ======>" + "\n")
                    current_bouquet.write("#SERVICE "+"1:0:"+hexa_to_bouquet(st)+":"+num_to_bouquet(lamedb_row[1])+":"+num_to_bouquet(lamedb_row[3])+":"+num_to_bouquet(lamedb_row[4])+":"+num_to_bouquet(lamedb_row[2])+":0:0:0:"+"\n")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description='Script to create bouquets for VU+ Ultimo.')
    bouquet_setting = arg_parser.add_mutually_exclusive_group()
    bouquet_setting_serv_type = arg_parser.add_mutually_exclusive_group(required=True)
    scrapping_setting = arg_parser.add_mutually_exclusive_group(required=True)
    arg_parser.add_argument('-s', '--scrap',
                            action='store_true',
                            help='to enable scrapping function of webpage https://en.kingofsat.net. If not enabled latest data in channels.csv are used')
    arg_parser.add_argument('-m', '--merge',
                            action='store_true',
                            help="To merge all bouquets in directory bouquets. It will create single bouquet named by user.")
    bouquet_setting.add_argument('-audio', '--audio_based',
                            action='store_true',
                            help='to create bouquets based on audio of channels. By default all possible bouquets are created.')
    bouquet_setting.add_argument('-custom', '--custom_based',
                            action='store_true',
                            help='to create bouquets based on category and audio preferences present in config.txt file. By default all possible bouquets are created.')
    bouquet_setting_serv_type.add_argument('-radio', '--radio_based',
                            action='store_true',
                            help='MANDATORY! To create RADIO bouquets.')
    bouquet_setting_serv_type.add_argument('-tv', '--tv_based',
                            action='store_true',
                            help='MANDATORY! To create TV bouquets.')
    scrapping_setting.add_argument('-freq', '--frequency',
                            action='store_true',
                            help='MANDATORY! To scrap webpage KingOfSat by frequency.')
    scrapping_setting.add_argument('-pack', '--packages',
                            action='store_true',
                            help='MANDATORY! To scrap webpage KingOfSat by packages.')
    args = arg_parser.parse_args()

    if args.scrap:
        # open .csv file
        with open("channels.csv", "w") as channels_csv:
            csv_writer = csv.writer(channels_csv, delimiter=';')
            csv_writer.writerow(["SID", "POS", "TID", "NID", "Name", "Country", "Category", "Audio"])
        main_url = "https://en.kingofsat.net/"
        satellites_xml = parse_config_file('-SATELLITESXML')[0]
        print("KingOfSat.net Web scraping has begun")
        result = browse_and_scrape(main_url, args)
        if not result:
            print("Web scraping is now complete!")
            print("All channel info is stored at channels.csv.")
        else:
            print(f"Oops, That doesn't seem right!!! - {result}")

    # scrapping is done
    # now do bouqueting
    # 1. load channel info from channels.csv and store them to dictionary
    channel_dict = create_channel_dict("channels.csv")
    print("Dictionary of scrapped channels created.")

    # 2. find matches between lamedb5 file and channel_dict
    lamedb5_path = parse_config_file('-LAMEDB5')
    create_bouquets(channel_dict, lamedb5_path[0], args)
