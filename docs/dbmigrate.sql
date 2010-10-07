
#version 1:
alter table waypoint add column "altitude" varchar(6) not null default '';

#version 2:
alter table "user" ADD lastlogin timestamp without time zone not null default '2010-07-19';

#version 3:
alter table "trip" ADD startfuel real not null default '0';

#version 4:
#adds notam_category_filter
#use paster setup-app for this
create table notam_category_filter ("user" varchar(32) not null primary key,"category" varchar not null primary key);
alter table notam_category_filter add primary key ("user","category");
alter table notam_category_filter add constraint notam_category_filter_user_fkey FOREIGN KEY ("user") REFERENCES "user"("user") ON UPDATE CASCADE ON DELETE CASCADE;

#version 5:
alter table "user" ADD "showobst" boolean not null default 'true'; 

#version 6:
#alter table waypoint add column landhere boolean not null default false;
#alter table "waypoint" drop column landhere;
#Add indexes to waypoint table, indexing on user and trip.

alter table aircraft add column atstype varchar(32) not null default 'ULAC';
alter table aircraft add column markings varchar(32) not null default 'W';
alter table "user" add column "phonenr" varchar(50);
alter table "user" add column "realname" varchar(100);
alter table "trip" drop column "startfuel";
alter table waypoint RENAME COLUMN ordinal TO "id";
alter table waypoint alter COLUMN id drop default;
alter table waypoint add column ordering integer;
update waypoint set ordering=id;
alter table waypoint ALTER COLUMN ordering set not null;





