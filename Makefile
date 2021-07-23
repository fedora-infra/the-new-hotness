up:
	docker-compose -f container-compose.yml up -d hotness
restart:
	docker-compose -f container-compose.yml restart
halt:
	docker-compose -f container-compose.yml down
bash:
	docker-compose -f container-compose.yml exec hotness bash -c "cat /app/.container/motd; bash;"
logs:
	docker-compose -f container-compose.yml logs -f

