define compose
	docker-compose -f container-compose.yml
endef

up:
	$(call compose) up -d hotness
restart:
	$(call compose) restart
halt:
	$(call compose) down
bash:
	$(call compose) exec hotness bash -c "cat /app/.container/motd; bash;"
logs:
	$(call compose) logs -f

