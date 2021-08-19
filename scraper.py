import requests
import time
import csv
import re
import argparse
from bs4 import BeautifulSoup

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

# prepare Country, Category
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

def scrape_and_write(soup, satellite):
    # find tables that contain channel elements
    html_tables = soup.find_all("table", class_="fl")
    for table in html_tables:

        html_frq_table = table.find_previous("table", class_="frq")
        tid, nid = get_tranponder_ids(html_frq_table)

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
                csv_writer.writerow([sid[item], int(float(satellite[:-1])*10), tid, nid, names[item], countries[item], categories[item], audios[item]])

def prepare_url_pos(pos):
    char_to_replace = {',': '.', '°': ''}
    for key, value in char_to_replace.items():
        pos = pos.replace(key, value)
    return pos

def browse_and_scrape(main_url, list_of_satellites):
    print(list_of_satellites)
    # prepare url for scraping
    for satellite in list_of_satellites:
        formated_sat = prepare_url_pos(satellite)
        url = main_url + "pos-" + formated_sat + ".php"
        try:
            html_text = requests.get(url).text
            # Prepare the soup
            soup = BeautifulSoup(html_text, "html.parser")
            print(f"Now Scraping - {url}")
            scrape_and_write(soup, formated_sat)
        except Exception as e:
            return e
    return True

# find all orbital possitions available in file satellites.xml
def find_orbital_pos(satellites_xml_path):
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
        return f"SID = {self.sid}; POS = {self.pos}; TID = {self.tid}; NID = {self.nid}; \
                Name = {self.name}; Country = {self.coutnr}; \
                Category = {self.category}; Languages = {self.languages}"

def calc_dict_key(channel):
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
            channel_dict[calc_dict_key(channel)] = channel
    return channel_dict

def create_bouquets(channel_dict, lamedb5):
    bouquets = []
    with open(lamedb5) as lamedb5_csv:
        csv_reader = csv.reader(lamedb5_csv, delimiter=':')
        for row in csv_reader:
            print(row)

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description='Script to create bouquets for VU+ Ultimo')
    arg_parser.add_argument('--scrap', '-s',
                            action='store_true')
    args = arg_parser.parse_args()

    if (args.scrap) :
        # open .csv file
        with open("channels.csv", "w") as channels_csv:
            csv_writer = csv.writer(channels_csv, delimiter=';')
            csv_writer.writerow(["SID", "POS", "TID", "NID", "Name", "Country", "Category", "Audio"])
        main_url = "https://en.kingofsat.net/"
        satellites_xml = "/home/stephenx/Dokumenty/python/Ultimo_Bouqeting/sample_data/ultimo/satellites.xml"
        list_of_satellites = find_orbital_pos(satellites_xml)
        print("KingOfSat.net Web scraping has begun")
        result = browse_and_scrape(main_url, list_of_satellites)
        if result == True:
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
    #create_bouquets(channel_dict, "/home/stephenx/Dokumenty/python/Ultimo_Bouqeting/sample_data/ultimo/lamedb5")
