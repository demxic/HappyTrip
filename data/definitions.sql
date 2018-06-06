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