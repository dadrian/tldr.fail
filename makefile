build:
	go version
	go run main.go > static/index.html

serve:
	go run main.go serve
