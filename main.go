package main

import (
	"bytes"
	_ "embed"
	"fmt"
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
			switch r.URL.Path {
			case "index.html", "", "/", "/index":
				t, data, err := reload()
				if err != nil {
					w.WriteHeader(500)
					w.Write([]byte(err.Error()))
					return
				}
				if err := t.Execute(w, data); err != nil {
					log.Printf("error writing template: %s", err)
				}
			default:
				w.WriteHeader(404)
				return
			}
		}))
	}()
	wg.Wait()
}

func reload() (*template.Template, map[string]any, error) {
	md, err := os.ReadFile("index.md")
	if err != nil {
		return nil, nil, fmt.Errorf("unable to read index.md: %w", err)
	}
	tmpl, err := os.ReadFile("index.html")
	if err != nil {
		return nil, nil, fmt.Errorf("unable to read index.html: %w", err)
	}
	css, err := os.ReadFile("index.css")
	if err != nil {
		return nil, nil, fmt.Errorf("unable to read index.css: %w", err)
	}
	return render(md, string(tmpl), string(css))
}

func render(md []byte, tmpl, css string) (*template.Template, map[string]any, error) {
	buf := bytes.Buffer{}
	if err := goldmark.Convert(md, &buf); err != nil {
		return nil, nil, fmt.Errorf("unable to render markdown: %w", err)
	}
	t, err := template.New("index.html").Parse(tmpl)
	if err != nil {
		return nil, nil, fmt.Errorf("unable to parse index.html", err)
	}
	data := map[string]any{
		"Content": buf.String(),
		"Css":     css,
	}
	return t, data, nil
}

func print(t *template.Template, data any) {
	if err := t.Execute(os.Stdout, data); err != nil {
		log.Fatalf("Failed to render index.html: %s", err)
	}
}

func main() {
	t, data, err := render(md, base, css)
	if err != nil {
		log.Fatalf("%s", err)
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
