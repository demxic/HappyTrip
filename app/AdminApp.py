from data.database import Database
from model.scheduleClasses import Airport

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")
source = "C:\\Users\\Xico\\PycharmProjects\\HappyTrip\\data\\iata_tzmap.txt"

with open(source, 'r') as f:
    for line in f.readlines():
        if "Merida" in line:
            print(line)
            iata_code, continent, tz_city = line.split()
            timezone = continent+'/'+tz_city
            viaticum_zone = input('Qué tipo de viático es? ')
            if viaticum_zone == 'x':
                pass
            else:
                airport = Airport(iata_code=iata_code, timezone=timezone,
                                  viaticum=viaticum_zone)
                airport.save_to_db()
