{%- set fqdn = [] %}
{%- set hostname = grains['id'] %}
{%- set domain = "etromb.local" %}
{%- set ldap_domain = "dc=etromb,dc=local" %}
{%- set fqdn = hostname + '.' + domain %}
{%- set realm = domain.upper()%}


globals:
    fqdn: '{{ fqdn }}'
    hostname: '{{ hostname }}'
    domain: '{{ domain }}'
    ldap_domain: '{{ ldap_domain }}'
    realm: '{{ realm }}'