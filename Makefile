up:
	docker-compose up -d
restart:
	docker-compose restart
halt:
	docker-compose down
bash:
	docker exec -it hotness bash
logs:
	docker-compose logs -f

