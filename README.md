This script is designed to poll information from the meraki API using an API key and an organization ID. 
It finds iterates through the networks and sums the sent and recieved data to be stored in an SQLite
database. This data can then be polled by Grafana by number to display the data.

Example SQL Queries in Grafana:

    SELECT sent, recv, time FROM networks WHERE number=1;

This selects all information on a specific network.

    SELECT name FROM networks WHERE number=1 LIMIT 1;

Selects the name of the network associated with the number, this can be used with Grafana's environmental 
variables to dynamically name each panel.

The Variables APIKEY and ORG_ID in the python script must be added manually for the script to work.