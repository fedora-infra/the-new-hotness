up:
	docker-compose up -d hotness
restart:
	docker-compose restart
halt:
	docker-compose down
bash:
	docker-compose exec hotness bash -c "cat /app/.container/motd; bash;"
logs:
	docker-compose logs -f

