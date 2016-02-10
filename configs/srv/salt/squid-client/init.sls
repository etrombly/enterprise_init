/etc/yum.repos.d/CentOS-Base.repo:
    file.managed:
        - source: salt://squid-client/files/CentOS-Base.repo

/etc/yum.conf:
    file.managed:
        - source: salt://squid-client/files/yum.conf
        - template: jinja
        - defaults:
            squid_ip: 192.168.0.6