DROP TABLE public.airports;
DROP TYPE viaticum;

CREATE TYPE viaticum AS ENUM ('high_cost', 'low_cost', 'superior_cost', 'border', 'usa', 'new_york', 'madrid', 'paris');
CREATE TYPE gposition AS ENUM ('EJE', 'SOB');

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
    OWNER to xico;
	

-- Table: public.routes

-- DROP TABLE public.routes;

CREATE TABLE public.routes
(
    route_id serial NOT NULL,
    name varchar(4) NOT NULL,
    origin character(3) NOT NULL,
    destination character(3) NOT NULL,
    CONSTRAINT routes_pkey PRIMARY KEY (route_id),
    CONSTRAINT routes_name_origin_destination_key UNIQUE (name, origin, destination),
    CONSTRAINT routes_destination_fkey FOREIGN KEY (destination)
        REFERENCES public.airports (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT routes_origin_fkey FOREIGN KEY (origin)
        REFERENCES public.airports (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.routes
    OWNER to xico;
	
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
    OWNER to xico;

-- Table: public.markers

-- DROP TABLE public.markers;

CREATE TABLE public.markers
(
    marker_id bigserial NOT NULL,
    route_id serial NOT NULL,
    begin timestamp without time zone NOT NULL,
    duration interval NOT NULL,
    CONSTRAINT markers_pkey PRIMARY KEY (marker_id),
    CONSTRAINT markers_route_id_begin_duration_key UNIQUE (route_id, begin, duration)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE public.markers
    OWNER to xico;

-- Table: public.reserves

-- DROP TABLE public.reserves;

CREATE TABLE public.reserves
(
    reserve_id bigserial NOT NULL,
    route_id serial NOT NULL,
    begin timestamp without time zone NOT NULL,
    duration interval NOT NULL,
    gposition gposition NOT NULL,
    CONSTRAINT reserves_pkey PRIMARY KEY (reserve_id),
    CONSTRAINT reserves_route_id_begin_duration_key UNIQUE (route_id, begin, duration)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE public.reserves
    OWNER to xico;

-- Table: public.flights

DROP TABLE public.duty_days;
DROP TABLE public.trips;
DROP TABLE public.flights;

CREATE TABLE public.flights
(
    flight_id bigserial NOT NULL,
    airline_iata_code character(2) NOT NULL DEFAULT 'AM',
    route_id serial NOT NULL,
    scheduled_begin timestamp without time zone NOT NULL,
    scheduled_block interval NOT NULL,
    equipment character(3),
    actual_begin timestamp without time zone,
    actual_block interval,
    CONSTRAINT flights_pkey PRIMARY KEY (flight_id),
    CONSTRAINT flights_airline_iata_code_route_id_scheduled_departure_date_key UNIQUE (airline_iata_code, route_id, scheduled_begin),
    CONSTRAINT flights_airline_iata_code_fkey FOREIGN KEY (airline_iata_code)
        REFERENCES public.airlines (iata_code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT flights_route_id_fkey FOREIGN KEY (route_id)
        REFERENCES public.routes (route_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT flights_equipment_fkey FOREIGN KEY (equipment)
        REFERENCES public.equipments (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
);

ALTER TABLE public.flights
    OWNER to xico;
	

-- Table: public.trips

-- DROP TABLE public.trips;

CREATE TABLE public.trips
(
    number smallint NOT NULL,
    dated date NOT NULL,
    mxn money,
    usd money,
	  red_eye money,
	  understaffed money,
    gposition gposition,
    CONSTRAINT unique_trip PRIMARY KEY (number, dated),
    CONSTRAINT valid_trip_id CHECK (number < 10000)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.trips
    OWNER to xico;
	
-- Table: public.duty_days

-- DROP TABLE public.duty_days;

CREATE TABLE public.duty_days
(
    duty_day_id bigserial NOT NULL,
    flight_id bigint NOT NULL,
    trip_id smallint NOT NULL,
    trip_date date NOT NULL,
    report time without time zone,
    rel time without time zone,
    dh boolean NOT NULL,
    CONSTRAINT duty_day_pkey PRIMARY KEY (duty_day_id),
	  CONSTRAINT flights_to_trip_in_duty_day UNIQUE (flight_id, trip_id, trip_date),
    CONSTRAINT duty_days_flight_id_fkey FOREIGN KEY (flight_id)
        REFERENCES public.flights (flight_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT duty_days_trip_id_fkey FOREIGN KEY (trip_date, trip_id)
        REFERENCES public.trips (dated, number) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT duty_day_id_check CHECK (trip_id < 10000)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.duty_days
    OWNER to xico;