DROP TABLE public.airports;
DROP TYPE viaticum;

CREATE TYPE viaticum AS ENUM ('high_cost', 'low_cost', 'superior_cost', 'border', 'usa', 'new_york', 'madrid', 'paris');


-- Table: public.airport

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