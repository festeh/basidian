package main

import (
	"flag"
	"log"
	"basidian/database"
	"basidian/routes"

	"github.com/gin-gonic/gin"
)

func main() {
	addr := flag.String("http", ":8090", "HTTP server address")
	dbPath := flag.String("db", "./pb_data/data.db", "SQLite database path")
	flag.Parse()

	// Initialize database
	if err := database.Init(*dbPath); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer database.Close()

	// Set up Gin router
	r := gin.Default()

	// Set up routes
	routes.Setup(r)
	log.Printf("Routes configured")

	log.Printf("Server starting on %s", *addr)
	if err := r.Run(*addr); err != nil {
		log.Fatal(err)
	}
}
