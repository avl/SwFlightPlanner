
#version 1:
alter table waypoint add column "altitude" varchar(6) not null default '';

#version 2:
alter table "user" ADD lastlogin timestamp without time zone not null default '2010-07-19';

#version 3:
alter table "trip" ADD startfuel real not null default '0';

