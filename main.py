import time, os, re
import mysql.connector
from urllib.request import urlopen, Request
from json import load
import folium
from geopy.geocoders import Nominatim


user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
loc = 'tail -f /var/log/auth.log Visualization'
title_html = '''
                <h3 align="center" style="font-size:33px; background-color:black; color:white; margin: 0;"><b>{}</b></h3>
             '''.format(loc)   

# SQL zugang
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="aplybot",
  database="map"
)
cursor = mydb.cursor()

# tail -f varriante aus google kopiert ka. geht
#Set the filename and open the file
filename = '/var/log/auth.log'
file = open(filename,'r')

#Find the size of the file and move to the end
st_results = os.stat(filename)
st_size = st_results[6]
file.seek(st_size)

def update_world(): # Kuckt ob ein ländercode mit lat_lon schon in world drinne ist und wenn nicht sucht er nach lat_lon und trägt sie ein 
    # Sql Shizzle
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="aplybot",
        database="map"
    )
    cursor = mydb.cursor()
    geolocator = Nominatim(user_agent="my-app")
    select_query = "SELECT country FROM data"
    cursor.execute(select_query)
    lands = cursor.fetchall()

    for land in lands:
        print(land)
        select_query_2 = "SELECT land, lat_lon FROM world WHERE land = %s"
        cursor.execute(select_query_2, (land[0],))
        land_isda = cursor.fetchone()

        if land_isda:
            print("Land already exists:", land_isda)
        else:
            
            location = geolocator.geocode(land[0])

            if location is not None:
                lat = str(location.latitude)
                lon = str(location.longitude)
                coordinates = lat + "," + lon
                insert_query = "INSERT INTO world (land, lat_lon) VALUES (%s, %s)"
                values = (land[0], coordinates)
                cursor.execute(insert_query, values)
                mydb.commit()
                print("Land inserted:", land, "Coordinates:", coordinates)
            else:
                print("Unable to fetch coordinates for:", land)

def ipInfo(addr=''): # sucht die ip adressen und verabeitet die ausgabe 
    print("fange an")
    from urllib.request import urlopen
    from json import load
    #kopiert vom beispiel ka. geht
    if addr == '':
        url = 'https://ipinfo.io/json'
    else:
        url = 'https://ipinfo.io/' + addr + '?token=a274d441de7394'
    req = Request(url, headers={'User-Agent': user_agent})
    res = urlopen(req)
    #Sucht in der Antwort nach den Schlüsselwärtern
    data = load(res)
    if 'loc' in data:
        loc = data['loc']
       # print('Location:', loc)
    if 'ip' in data:
        ip = data['ip']
        #print('ip:', ip)
    if 'city' in data:
        city = data['city']
        #print('ip:', ip)
    if 'region' in data:
        region = data['region']
        #print('ip:', ip)
    if 'country' in data:
        country = data['country']
        #print('ip:', ip)

    time.sleep(5)
    
    select_query = "SELECT ip FROM data WHERE ip = %s"
    cursor.execute(select_query, (ip,))
    existing_ip = cursor.fetchone()
    if existing_ip:
        pass
        
    else:
        try:
            insert_query = "INSERT INTO data (ip, lat_long, city, region, country) VALUES (%s, %s, %s, %s, %s)"
            values = (ip, loc, city, region, country)
            cursor.execute(insert_query, values)
            mydb.commit()
            print("IP inserted into the database:", ip)
            print ("IP: ",ip," lat/long: ",loc," City: ",city," Region: ",region," Land: ", country )
            cursor.close()
            update_world()
            karte()
        except:
            print("hänger")
            cursor.close()
            pass
    
def karte(): # Erstellt die karte und Layermenü

    #Datenbank shizzle
    cursor = mydb.cursor()
    select_query = "SELECT lat_long, city, country FROM data"
    cursor.execute(select_query)
    locations = cursor.fetchall()
    # Karte erstellen
    map = folium.Map(location=[34.7500, 10.7200], zoom_start=3, tiles="stamentoner")


    # Layer Checkbox
    all_group = folium.FeatureGroup(name="All",overlay=True, show=True).add_to(map)
    lines = folium.FeatureGroup(name="Lines",overlay=True, show=False).add_to(map)

    


    # Lat/Long-Position hinzufügen
    for location in locations:
        coordinates = location[0].split(',')
        if len(coordinates) == 2:
            lat = float(coordinates[0])
            lon = float(coordinates[1])
            city = location[1]
            country = location[2]
            
 
            all_group.add_child(folium.Marker(icon=folium.Icon(color='red'), location=[lat, lon], tooltip=f"{city}, {country}").add_to(map))
            lines.add_child(folium.PolyLine(locations=[[49.3988, 8.6724], [lat, lon]],color='yellow',weight=1)) 
    # Menü / Layer Control anpassen
    layer_control = folium.LayerControl(collapsed=True, position='topright',name='Layer Control Menu')
    layer_control.add_to(map)
    # CSS für die Menügröße
    css = """
        .leaflet-control-layers {
            transform: scale(1.5);
            right: 90px !important;
            left: auto !important;
            top: 50px !important;
        }
        """
    element = folium.Element('<style>{}</style>'.format(css))
    map.get_root().html.add_child(element)
    map.get_root().html.add_child(folium.Element(title_html))


        
    map.save('/var/www/html/index.html')
    print("Map newly rendered")

counter = 0

while 1: # Mainloop
    where = file.tell()
    line = file.readline()
    if not line:
        time.sleep(1)
        file.seek(where)
    else:
        ip_address = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
        if ip_address:
            ip = ip_address.group()
            cursor = mydb.cursor()
            select_query = "SELECT ip FROM data WHERE ip = %s"
            cursor.execute(select_query, (ip,))
            existing_ip = cursor.fetchone()
            
            if existing_ip:
                counter = counter +1
                print("IP :", ip , "added +1","counter=",counter)
                add_ping = "UPDATE data SET ping = IFNULL(ping, 0) + 1 WHERE ip = %s;"
                cursor.execute(add_ping, (ip,))
                cursor.close()
                if counter==500:
                    counter = 0
                    update_world()
                    karte()
                    print ("counter erreicht shizzle neu berrechnet")



                pass

            else:
                ipInfo(ip)
            

            
