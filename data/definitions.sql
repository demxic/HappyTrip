DROP TABLE public.airports;
DROP TYPE viaticum;

CREATE TYPE viaticum AS ENUM ('high_cost', 'low_cost', 'superior_cost', 'border', 'usa', 'new_york', 'madrid', 'paris');


-- Table: public.airports

CREATE TABLE public.airports
(
    iata_code character(3) NOT NULL,
    time_zone character varying NOT NULL,
    viaticum_zone viaticum NOT NULL,
    PRIMARY KEY (iata_code)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE public.airports
    OWNER to postgres;
	

-- Table: public.routes

-- DROP TABLE public.routes;

CREATE TABLE public.routes
(
    id smallint NOT NULL DEFAULT nextval('routes_id_seq'::regclass),
    flight_number character(4) COLLATE pg_catalog."default" NOT NULL,
    departure_airport character(3) COLLATE pg_catalog."default" NOT NULL,
    arrival_airport character(3) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT routes_pkey PRIMARY KEY (id),
    CONSTRAINT routes_flight_number_departure_airport_arrival_airport_key UNIQUE (flight_number, departure_airport, arrival_airport),
    CONSTRAINT routes_arrival_airport_fkey FOREIGN KEY (arrival_airport)
        REFERENCES public.airports (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT routes_departure_airport_fkey FOREIGN KEY (departure_airport)
        REFERENCES public.airlines (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.routes
    OWNER to postgres;
	
-- Table: public.equipments

-- DROP TABLE public.equipments;

CREATE TABLE public.equipments
(
    code character(3) COLLATE pg_catalog."default" NOT NULL,
    cabin_members smallint,
    CONSTRAINT equipments_pkey PRIMARY KEY (code)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.equipments
    OWNER to postgres;
	
-- Table: public.flights

DROP TABLE public.duty_days;
DROP TABLE public.trips;
DROP TABLE public.flights;

CREATE TABLE public.flights
(
    id bigserial NOT NULL,
    airline_iata_code character(2) COLLATE pg_catalog."default" NOT NULL DEFAULT 'AM'::bpchar,
    route_id smallint NOT NULL,
    scheduled_departure_date date NOT NULL,
    scheduled_departure_time time without time zone NOT NULL,
    scheduled_block interval NOT NULL,
    scheduled_equipment character(3) COLLATE pg_catalog."default",
    actual_departure_date date,
    actual_departure_time time without time zone,
    actual_block interval,
    actual_equipment character(3) COLLATE pg_catalog."default",
    CONSTRAINT flights_pkey PRIMARY KEY (id),
    CONSTRAINT flights_airline_iata_code_route_id_scheduled_departure_date_key UNIQUE (airline_iata_code, route_id, scheduled_departure_date, scheduled_departure_time),
    CONSTRAINT flights_actual_equipment_fkey FOREIGN KEY (actual_equipment)
        REFERENCES public.equipments (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT flights_airline_iata_code_fkey FOREIGN KEY (airline_iata_code)
        REFERENCES public.airlines (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT flights_route_id_fkey FOREIGN KEY (route_id)
        REFERENCES public.routes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT flights_scheduled_equipment_fkey FOREIGN KEY (scheduled_equipment)
        REFERENCES public.equipments (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.flights
    OWNER to postgres;
	

-- Table: public.trips

-- DROP TABLE public.trips;

CREATE TABLE public.trips
(
    id smallint NOT NULL,
    dated date NOT NULL,
    mxn money,
    usd money,
	red_eye money,
	understaffed money,
    "position" character varying COLLATE pg_catalog."default",
    CONSTRAINT unique_trip PRIMARY KEY (id, dated),
    CONSTRAINT valid_trip_id CHECK (id < 10000)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.trips
    OWNER to postgres;
	
-- Table: public.duty_days

-- DROP TABLE public.duty_days;

CREATE TABLE public.duty_days
(
    id bigserial NOT NULL,
    flight_id bigint NOT NULL,
    trip_id smallint NOT NULL,
    trip_date date NOT NULL,
    report time without time zone,
    rel time without time zone,
    dh boolean NOT NULL,
    CONSTRAINT duty_days_pkey PRIMARY KEY (id),
	CONSTRAINT flights_to_trip_in_duty_day UNIQUE (flight_id, trip_id, trip_date),
    CONSTRAINT duty_days_flight_id_fkey FOREIGN KEY (flight_id)
        REFERENCES public.flights (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT duty_days_trip_id_fkey FOREIGN KEY (trip_date, trip_id)
        REFERENCES public.trips (dated, id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT duty_days_id_check CHECK (trip_id < 10000)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.duty_days
    OWNER to postgres;