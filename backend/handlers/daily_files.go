package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"basidian/database"
	"sort"
	"time"

	"github.com/gin-gonic/gin"
)

// DailyNote represents a daily note
type DailyNote struct {
	ID        string  `json:"id"`
	Date      string  `json:"date"`
	Name      string  `json:"name"`
	Path      string  `json:"path"`
	Content   string  `json:"content,omitempty"`
	CreatedAt *string `json:"created_at,omitempty"`
	UpdatedAt *string `json:"updated_at,omitempty"`
}

// DailyYear represents a year with notes
type DailyYear struct {
	Year  string      `json:"year"`
	Notes []DailyNote `json:"notes"`
}

// DailyListResponse is the response for listing all daily notes
type DailyListResponse struct {
	Years []DailyYear `json:"years"`
}

// dateToPath converts YYYY-MM-DD to /daily/YYYY-MM-DD.md path
func dateToPath(dateStr string) string {
	return fmt.Sprintf("/daily/%s.md", dateStr)
}

// ensureDailyFolder creates the /daily folder if it doesn't exist
func ensureDailyFolder() error {
	var exists bool
	err := database.DB.QueryRow("SELECT 1 FROM fs_nodes WHERE path = '/daily'").Scan(&exists)
	if err == sql.ErrNoRows {
		id := database.GenerateID()
		now := time.Now().Format(time.RFC3339)
		_, err = database.DB.Exec(`
			INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
			VALUES (?, 'folder', 'daily', '/daily', '/', '', 0, 0, ?, ?)
		`, id, now, now)
		if err != nil {
			return err
		}
		log.Printf("Created /daily folder")
	}
	return nil
}

// GetDailyFile returns a daily note for a specific date, creates if not exists
func GetDailyFile(c *gin.Context) {
	dateStr := c.Param("date")

	t, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid date format. Use YYYY-MM-DD"})
		return
	}

	path := dateToPath(dateStr)
	name := fmt.Sprintf("%s.md", dateStr)

	// Check if note exists
	var note DailyNote
	var created, updated string
	err = database.DB.QueryRow(`
		SELECT id, path, name, content, created, updated
		FROM fs_nodes
		WHERE path = ? AND is_daily = 1
	`, path).Scan(&note.ID, &note.Path, &note.Name, &note.Content, &created, &updated)

	if err == sql.ErrNoRows {
		// Create new daily note
		if err := ensureDailyFolder(); err != nil {
			c.JSON(500, gin.H{"error": "Failed to create daily folder"})
			return
		}

		id := database.GenerateID()
		now := time.Now().Format(time.RFC3339)
		content := fmt.Sprintf("# %s\n\n", t.Format("January 2, 2006"))

		_, err = database.DB.Exec(`
			INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
			VALUES (?, 'file', ?, ?, '/daily', ?, 1, 0, ?, ?)
		`, id, name, path, content, now, now)

		if err != nil {
			log.Printf("GetDailyFile: Insert failed: %v", err)
			c.JSON(500, gin.H{"error": "Failed to create daily note"})
			return
		}

		log.Printf("Created daily note: %s", path)
		c.JSON(201, DailyNote{
			ID:        id,
			Date:      dateStr,
			Name:      name,
			Path:      path,
			Content:   content,
			CreatedAt: &now,
			UpdatedAt: &now,
		})
		return
	}

	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch daily note"})
		return
	}

	note.Date = dateStr
	if created != "" {
		note.CreatedAt = &created
	}
	if updated != "" {
		note.UpdatedAt = &updated
	}

	c.JSON(200, note)
}

// UpdateDailyFile updates a daily note's content
func UpdateDailyFile(c *gin.Context) {
	dateStr := c.Param("date")

	t, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid date format. Use YYYY-MM-DD"})
		return
	}

	var req struct {
		Content string `json:"content"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	path := dateToPath(dateStr)
	name := fmt.Sprintf("%s.md", dateStr)
	now := time.Now().Format(time.RFC3339)

	// Check if exists
	var id string
	err = database.DB.QueryRow("SELECT id FROM fs_nodes WHERE path = ? AND is_daily = 1", path).Scan(&id)

	if err == sql.ErrNoRows {
		// Create new
		if err := ensureDailyFolder(); err != nil {
			c.JSON(500, gin.H{"error": "Failed to create daily folder"})
			return
		}

		id = database.GenerateID()
		content := req.Content
		if content == "" {
			content = fmt.Sprintf("# %s\n\n", t.Format("January 2, 2006"))
		}

		_, err = database.DB.Exec(`
			INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
			VALUES (?, 'file', ?, ?, '/daily', ?, 1, 0, ?, ?)
		`, id, name, path, content, now, now)

		if err != nil {
			c.JSON(500, gin.H{"error": "Failed to create daily note"})
			return
		}

		log.Printf("Created daily note: %s", path)
		c.JSON(201, DailyNote{
			ID:        id,
			Date:      dateStr,
			Name:      name,
			Path:      path,
			Content:   content,
			CreatedAt: &now,
			UpdatedAt: &now,
		})
		return
	}

	// Update existing
	_, err = database.DB.Exec(`
		UPDATE fs_nodes SET content = ?, updated = ? WHERE id = ?
	`, req.Content, now, id)

	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to update daily note"})
		return
	}

	// Fetch updated
	var note DailyNote
	var created, updated string
	database.DB.QueryRow(`
		SELECT id, path, name, content, created, updated
		FROM fs_nodes WHERE id = ?
	`, id).Scan(&note.ID, &note.Path, &note.Name, &note.Content, &created, &updated)

	note.Date = dateStr
	if created != "" {
		note.CreatedAt = &created
	}
	if updated != "" {
		note.UpdatedAt = &updated
	}

	log.Printf("Updated daily note: %s", path)
	c.JSON(200, note)
}

// ListDailyFiles returns all daily notes organized by year
func ListDailyFiles(c *gin.Context) {
	rows, err := database.DB.Query(`
		SELECT id, path, name, created, updated
		FROM fs_nodes
		WHERE is_daily = 1 AND type = 'file'
		ORDER BY path DESC
	`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch daily notes"})
		return
	}
	defer rows.Close()

	// Group by year
	yearMap := make(map[string][]DailyNote)

	for rows.Next() {
		var note DailyNote
		var created, updated string
		if err := rows.Scan(&note.ID, &note.Path, &note.Name, &created, &updated); err != nil {
			continue
		}

		// Extract date from path: /daily/YYYY-MM-DD.md (length = 20)
		if len(note.Path) >= 20 {
			note.Date = note.Path[7:17] // Extract YYYY-MM-DD
			year := note.Date[:4]

			if created != "" {
				note.CreatedAt = &created
			}
			if updated != "" {
				note.UpdatedAt = &updated
			}

			yearMap[year] = append(yearMap[year], note)
		}
	}

	// Convert to response format
	response := DailyListResponse{Years: []DailyYear{}}

	for year, notes := range yearMap {
		// Sort notes by date descending
		sort.Slice(notes, func(i, j int) bool {
			return notes[i].Date > notes[j].Date
		})
		response.Years = append(response.Years, DailyYear{Year: year, Notes: notes})
	}

	// Sort years descending
	sort.Slice(response.Years, func(i, j int) bool {
		return response.Years[i].Year > response.Years[j].Year
	})

	c.JSON(200, response)
}

// DeleteDailyFile deletes a daily note
func DeleteDailyFile(c *gin.Context) {
	dateStr := c.Param("date")

	_, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid date format. Use YYYY-MM-DD"})
		return
	}

	path := dateToPath(dateStr)

	result, err := database.DB.Exec("DELETE FROM fs_nodes WHERE path = ? AND is_daily = 1", path)
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to delete daily note"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Daily note not found"})
		return
	}

	log.Printf("Deleted daily note: %s", path)
	c.Status(204)
}

// GetDailyConfig returns the daily notes configuration (SQLite-based, no path needed)
func GetDailyConfig(c *gin.Context) {
	var count int
	database.DB.QueryRow("SELECT COUNT(*) FROM fs_nodes WHERE is_daily = 1 AND type = 'file'").Scan(&count)

	c.JSON(200, gin.H{
		"storage": "sqlite",
		"count":   count,
	})
}

// SetDailyConfig is a no-op since we're using SQLite (kept for API compatibility)
func SetDailyConfig(c *gin.Context) {
	c.JSON(200, gin.H{
		"storage": "sqlite",
		"message": "Daily notes are stored in SQLite database",
	})
}
