import time, os, re
import mysql.connector
from urllib.request import urlopen, Request
from json import load
import folium

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="aplybot",
  database="map"
)
#Set the filename and open the file
filename = '/var/log/auth.log'
file = open(filename,'r')

#Find the size of the file and move to the end
st_results = os.stat(filename)
st_size = st_results[6]
file.seek(st_size)

def ipInfo(addr=''):
    print("fange an")
    from urllib.request import urlopen
    from json import load
    
    if addr == '':
        url = 'https://ipinfo.io/json'
    else:
        url = 'https://ipinfo.io/' + addr + '?token=a274d441de7394'
    req = Request(url, headers={'User-Agent': user_agent})
    res = urlopen(req)
    
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
    #print ("IP: ",ip," lat/long: ",loc," City: ",city," Region: ",region," Land: ", country )
    time.sleep(5)
    cursor = mydb.cursor()
    select_query = "SELECT ip FROM data WHERE ip = %s"
    cursor.execute(select_query, (ip,))
    existing_ip = cursor.fetchone()
    if existing_ip:
        #print("IP already exists in the database:", ip)
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
            karte()
        except:
            print("hänger")
            pass
    
    

def karte():
    cursor = mydb.cursor()
    select_query = "SELECT lat_long, city, country FROM data"
    cursor.execute(select_query)
    locations = cursor.fetchall()

    # Karte erstellen
    map = folium.Map(location=[49.3988, 8.6724], zoom_start=3)



    # Marker für jede Lat/Long-Position hinzufügen
    for location in locations:
        coordinates = location[0].split(',')
        if len(coordinates) == 2:
            lat = float(coordinates[0])
            lon = float(coordinates[1])
            city = location[1]
            country = location[2]
            print("lat", lat)
            print("lon", lon)
            marker = folium.Marker(location=[lat, lon])
            marker.add_to(map)
            folium.Marker(location=[lat, lon], tooltip=f"{city}, {country}").add_to(map)
            line = folium.PolyLine(
                locations=[[49.3988, 8.6724], [lat, lon]],
                color='red',
                weight=2
            )
            line.add_to(map)
        
    map.save('/var/www/html/index.html')

    

    #druckt alles
   # for attr in data.keys():
        #will print the data line by line
    #    print(attr,' '*13+'\t->\t',data[attr])

while 1:
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
                print("IP already exists in the database:", ip)
                pass
            else:
                ipInfo(ip)