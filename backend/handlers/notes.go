package handlers

import (
	"database/sql"
	"log"
	"basidian/database"
	"time"

	"github.com/gin-gonic/gin"
)

type Note struct {
	ID        string  `json:"id"`
	Title     string  `json:"title"`
	Content   string  `json:"content"`
	Date      string  `json:"date"`
	CreatedAt *string `json:"created_at"`
	UpdatedAt *string `json:"updated_at"`
}

type NoteRequest struct {
	Title   string `json:"title"`
	Content string `json:"content"`
	Date    string `json:"date"`
}

func GetNotes(c *gin.Context) {
	log.Printf("GetNotes: Fetching all notes")

	rows, err := database.DB.Query(`
		SELECT id, title, content, date, created, updated
		FROM notes
		ORDER BY date DESC
	`)
	if err != nil {
		log.Printf("GetNotes: Query failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to fetch notes"})
		return
	}
	defer rows.Close()

	notes := make([]Note, 0)
	for rows.Next() {
		var n Note
		var created, updated string
		if err := rows.Scan(&n.ID, &n.Title, &n.Content, &n.Date, &created, &updated); err != nil {
			log.Printf("GetNotes: Scan failed: %v", err)
			continue
		}
		if created != "" {
			n.CreatedAt = &created
		}
		if updated != "" {
			n.UpdatedAt = &updated
		}
		notes = append(notes, n)
	}

	log.Printf("GetNotes: Found %d notes", len(notes))
	c.JSON(200, notes)
}

func GetNote(c *gin.Context) {
	id := c.Param("id")

	var n Note
	var created, updated string
	err := database.DB.QueryRow(`
		SELECT id, title, content, date, created, updated
		FROM notes
		WHERE id = ?
	`, id).Scan(&n.ID, &n.Title, &n.Content, &n.Date, &created, &updated)

	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Note not found"})
		return
	}
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch note"})
		return
	}

	if created != "" {
		n.CreatedAt = &created
	}
	if updated != "" {
		n.UpdatedAt = &updated
	}

	c.JSON(200, n)
}

func CreateNote(c *gin.Context) {
	var req NoteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	id := database.GenerateID()
	now := time.Now().Format(time.RFC3339)

	date := req.Date
	if date == "" {
		date = time.Now().Format("2006-01-02")
	}

	_, err := database.DB.Exec(`
		INSERT INTO notes (id, title, content, date, created, updated)
		VALUES (?, ?, ?, ?, ?, ?)
	`, id, req.Title, req.Content, date, now, now)

	if err != nil {
		log.Printf("CreateNote: Insert failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to create note"})
		return
	}

	note := Note{
		ID:        id,
		Title:     req.Title,
		Content:   req.Content,
		Date:      date,
		CreatedAt: &now,
		UpdatedAt: &now,
	}

	log.Printf("CreateNote: Created note %s", id)
	c.JSON(201, note)
}

func UpdateNote(c *gin.Context) {
	id := c.Param("id")

	var req NoteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	// Check if note exists
	var exists bool
	err := database.DB.QueryRow("SELECT 1 FROM notes WHERE id = ?", id).Scan(&exists)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Note not found"})
		return
	}

	now := time.Now().Format(time.RFC3339)

	_, err = database.DB.Exec(`
		UPDATE notes
		SET title = ?, content = ?, date = ?, updated = ?
		WHERE id = ?
	`, req.Title, req.Content, req.Date, now, id)

	if err != nil {
		log.Printf("UpdateNote: Update failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to update note"})
		return
	}

	// Fetch updated record
	var n Note
	var created, updated string
	database.DB.QueryRow(`
		SELECT id, title, content, date, created, updated
		FROM notes WHERE id = ?
	`, id).Scan(&n.ID, &n.Title, &n.Content, &n.Date, &created, &updated)

	if created != "" {
		n.CreatedAt = &created
	}
	if updated != "" {
		n.UpdatedAt = &updated
	}

	log.Printf("UpdateNote: Updated note %s", id)
	c.JSON(200, n)
}

func DeleteNote(c *gin.Context) {
	id := c.Param("id")

	// Check if note exists
	var exists bool
	err := database.DB.QueryRow("SELECT 1 FROM notes WHERE id = ?", id).Scan(&exists)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Note not found"})
		return
	}

	_, err = database.DB.Exec("DELETE FROM notes WHERE id = ?", id)
	if err != nil {
		log.Printf("DeleteNote: Delete failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to delete note"})
		return
	}

	log.Printf("DeleteNote: Deleted note %s", id)
	c.Status(204)
}

func GetNotesByDate(c *gin.Context) {
	dateStr := c.Param("date")

	_, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid date format. Use YYYY-MM-DD"})
		return
	}

	rows, err := database.DB.Query(`
		SELECT id, title, content, date, created, updated
		FROM notes
		WHERE date LIKE ?
		ORDER BY created DESC
	`, dateStr+"%")
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch notes"})
		return
	}
	defer rows.Close()

	notes := make([]Note, 0)
	for rows.Next() {
		var n Note
		var created, updated string
		if err := rows.Scan(&n.ID, &n.Title, &n.Content, &n.Date, &created, &updated); err != nil {
			continue
		}
		if created != "" {
			n.CreatedAt = &created
		}
		if updated != "" {
			n.UpdatedAt = &updated
		}
		notes = append(notes, n)
	}

	c.JSON(200, notes)
}

func SearchNotes(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(400, gin.H{"error": "Search query is required"})
		return
	}

	searchPattern := "%" + query + "%"

	rows, err := database.DB.Query(`
		SELECT id, title, content, date, created, updated
		FROM notes
		WHERE title LIKE ? OR content LIKE ?
		ORDER BY date DESC
	`, searchPattern, searchPattern)
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to search notes"})
		return
	}
	defer rows.Close()

	notes := make([]Note, 0)
	for rows.Next() {
		var n Note
		var created, updated string
		if err := rows.Scan(&n.ID, &n.Title, &n.Content, &n.Date, &created, &updated); err != nil {
			continue
		}
		if created != "" {
			n.CreatedAt = &created
		}
		if updated != "" {
			n.UpdatedAt = &updated
		}
		notes = append(notes, n)
	}

	c.JSON(200, notes)
}
