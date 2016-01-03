/etc/sssd/sssd.conf:
    file.managed:
        - source: salt://ipa-client/files/sssd.conf
        - user: root
        - group: root
        - mode: 600
        - template: jinja
        - defaults:
            hostname: {{ pillar['globals']['hostname'] }}
            fqdn: {{ pillar['globals']['fqdn'] }}
            domain: {{ pillar['globals']['domain'] }}
            ldap_domain: {{ pillar['globals']['ldap_domain'] }}
            realm: {{ pillar['globals']['realm'] }}

/etc/pam.d:
    file.recurse:
        - source: salt://ipa-client/files/pam.d
        - user: root
        - group: root

/etc/nscd.conf:
    file.managed:
        - source: salt://ipa-client/files/nscd.conf
        - user: root
        - group: root
        - mode: 744

/etc/nsswitch.conf:
    file.managed:
        - source: salt://ipa-client/files/nsswitch.conf
        - user: root
        - group: root
        - mode: 744

/etc/krb5.conf:
    file.managed:
        - source: salt://ipa-client/files/krb5.conf
        - user: root
        - group: root
        - mode: 744
        - template: jinja
        - defaults:
            domain: {{ pillar['globals']['domain'] }}
            realm: {{ pillar['globals']['realm'] }}

sssd:
    service.running:
        - enable: True
