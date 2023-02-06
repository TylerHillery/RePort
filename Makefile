docker-build-dev:
	docker build --target development -t portfolio-rebalancer-image --file docker/Dockerfile .

docker-run-dev:
	docker run --name portfolio-rebalancer-container -p 8501:8501 -d portfolio-rebalancer-image