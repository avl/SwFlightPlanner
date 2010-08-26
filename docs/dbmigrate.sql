
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


