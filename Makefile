up:
	docker-compose up -d
restart:
	docker-compose restart
halt:
	docker-compose down
bash:
	docker-compose exec hotness bash -c "cat /etc/motd; bash;"
logs:
	docker-compose logs -f

