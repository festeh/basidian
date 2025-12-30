package routes

import (
	"basidian/handlers"

	"github.com/gin-gonic/gin"
)

func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(200)
			return
		}

		c.Next()
	}
}

func Setup(r *gin.Engine) {
	r.Use(CORSMiddleware())

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "rumi-backend"})
	})

	// Notes API
	r.GET("/api/notes", handlers.GetNotes)
	r.POST("/api/notes", handlers.CreateNote)
	r.GET("/api/notes/:id", handlers.GetNote)
	r.PUT("/api/notes/:id", handlers.UpdateNote)
	r.DELETE("/api/notes/:id", handlers.DeleteNote)
	r.GET("/api/notes/date/:date", handlers.GetNotesByDate)
	r.GET("/api/search", handlers.SearchNotes)

	// Filesystem API
	r.GET("/api/fs/tree", handlers.GetTree)
	r.GET("/api/fs/node", handlers.GetNode)
	r.GET("/api/fs/node/:id", handlers.GetNodeById)
	r.POST("/api/fs/node", handlers.CreateNode)
	r.PUT("/api/fs/node/:id", handlers.UpdateNode)
	r.DELETE("/api/fs/node/:id", handlers.DeleteNode)
	r.POST("/api/fs/move/:id", handlers.MoveNode)
	r.GET("/api/fs/search", handlers.SearchFiles)

	// Daily notes (filesystem-based)
	r.GET("/api/daily", handlers.ListDailyFiles)
	r.GET("/api/daily/config", handlers.GetDailyConfig)
	r.PUT("/api/daily/config", handlers.SetDailyConfig)
	r.GET("/api/daily/:date", handlers.GetDailyFile)
	r.PUT("/api/daily/:date", handlers.UpdateDailyFile)
	r.DELETE("/api/daily/:date", handlers.DeleteDailyFile)
}
