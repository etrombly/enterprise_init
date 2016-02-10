squid:
    pkg.installed: []
    service.running:
        - enable: True

/etc/squid/squid.conf:
    file.managed:
        - source: salt://squid/files/squid.conf
        - require:
            - pkg: squid