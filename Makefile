install:
	install -D -p -m 0644 config.ini $(DESTDIR)/etc/registrar_agent/config.ini
	install -D -p -m 0755 registrar_agent.py $(DESTDIR)/usr/sbin/registrar_agent
	install -D -p -m 0755 registrar_agent.init $(DESTDIR)/etc/rc.d/init.d/registrar_agent
	install -d $(DESTDIR)/var/run/registrar_agent
clean:
	@rm -f *~
