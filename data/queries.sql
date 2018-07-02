INSERT INTO public.airports 
VALUES ('MEX', 'America/Mexico_City', 'low_cost')

-- Show routes by flight_number ascending
SELECT flight_number, departure_airport, arrival_airport FROM public.routes
ORDER BY flight_number ASC 

-- Select route_id
SELECT id from public.routes
WHERE routes.flight_number = '0786' AND routes.departure_airport = 'GDL' AND routes.arrival_airport = 'FAT';


-- Insert into flights table
INSERT INTO public.flights(
	airline_iata_code, route_id, scheduled_departure_date, scheduled_departure_time, scheduled_block, scheduled_equipment)
	VALUES ('AM', 1, '6/28/2018', '18:35', '11:05', '789');
	
	
-- Show flights 
SELECT airline_iata_code AS airline, flight_number as "FLT", scheduled_departure_date AS "dated",
		departure_airport AS origin, arrival_airport AS destination,
	   scheduled_departure_time AS ETD, 
	   (scheduled_departure_time + scheduled_block) as ETA, scheduled_equipment AS EQ
FROM public.flights
JOIN public.routes
ON routes.id = route_id
ORDER BY 
	"FLT" ASC, 
	 "dated" ASC;

-- Show trips
SELECT trip_id, trip_date, report, scheduled_departure_date as "dated", dh, airline_iata_code as "airline", 
		flight_number as "FLT", departure_airport as origin, scheduled_departure_time as "ETD", 
		arrival_airport as destination, (scheduled_departure_time + scheduled_block) as "ETA", 
		rel as "release", scheduled_equipment as "EQ" FROM public.duty_days
INNER JOIN public.flights ON flight_id = flights.id
INNER JOIN public.routes ON route_id = routes.id
ORDER BY trip_id, trip_date, dated, "ETD" ASC;


-- Show trip
SELECT * FROM public.duty_days
INNER JOIN public.flights ON flight_id = flights.id
WHERE trip_id = '3939' AND trip_date = '2018-06-20'
ORDER BY scheduled_departure_date, scheduled_departure_time ASC;


-- How many trips stored by position
SELECT position,
 COUNT (position)
FROM public.trips
GROUP BY
 position;


SELECT * FROM public.flights
WHERE id = 7409;
