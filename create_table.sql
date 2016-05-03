-- Table: twitter_userdata

-- DROP TABLE twitter_userdata;

CREATE TABLE twitter_userdata
(
  id_str character varying NOT NULL,
  screen_name character varying,
  followers_count integer,
  statuses_count integer,
  favourites_count integer,
  friends_count integer,
  CONSTRAINT twitter_userdata_pkey PRIMARY KEY (id_str)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE twitter_userdata
  OWNER TO aic_group;

-- Index: screen_name_index

-- DROP INDEX screen_name_index;

CREATE INDEX screen_name_index
  ON twitter_userdata
  USING hash
  (screen_name COLLATE pg_catalog."default");