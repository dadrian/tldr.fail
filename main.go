package main

import (
	"bytes"
	_ "embed"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"text/template"

	"github.com/yuin/goldmark"
)

//go:embed index.md
var md []byte

//go:embed index.css
var css string

//go:embed index.html
var base string

func serve(t *template.Template, data any) {
	buf := bytes.Buffer{}
	if err := t.Execute(&buf, data); err != nil {
		log.Fatalf("unable to render index.md: %s", err)
	}
	wg := sync.WaitGroup{}
	wg.Add(1)

	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt)

	go func() {
		defer wg.Done()
		<-done
	}()
	go func() {
		defer wg.Done()
		log.Printf("%s", "starting server on localhost:8080")
		http.ListenAndServe("localhost:8080", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			log.Printf("%s %s", r.Method, r.URL.Path)
			w.Write(buf.Bytes())
		}))
	}()
	wg.Wait()
}

func print(t *template.Template, data any) {
	if err := t.Execute(os.Stdout, data); err != nil {
		log.Fatalf("Failed to render index.html: %s", err)
	}
}

func main() {
	buf := bytes.Buffer{}
	if err := goldmark.Convert(md, &buf); err != nil {
		log.Fatalf("Invalid index.md: %s", err)
	}
	t := template.Must(template.New("index.html").Parse(base))
	data := map[string]any{
		"Content": buf.String(),
		"Css":     css,
	}
	if len(os.Args) <= 1 {
		print(t, &data)
	}

	if len(os.Args) > 1 && os.Args[1] == "serve" {
		serve(t, &data)
	}
	if len(os.Args) > 1 && os.Args[1] == "render" {
		print(t, &data)
	}

}
