sudo su postgres bash -c 'echo "drop database flightplanner;" | psql'
sudo su postgres bash -c 'echo "create database flightplanner;" | psql'
sudo su postgres bash -c 'echo "grant all on database flightplanner to flightplanner;" | psql'
#paster setup-app development.ini

