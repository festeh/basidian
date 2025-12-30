package handlers

import (
	"database/sql"
	"log"
	"basidian/database"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type FsNode struct {
	ID         string  `json:"id"`
	Type       string  `json:"type"`
	Name       string  `json:"name"`
	Path       string  `json:"path"`
	ParentPath string  `json:"parent_path"`
	Content    string  `json:"content"`
	IsDaily    bool    `json:"is_daily"`
	SortOrder  int     `json:"sort_order"`
	CreatedAt  *string `json:"created_at"`
	UpdatedAt  *string `json:"updated_at"`
}

type FsNodeRequest struct {
	Type       string `json:"type"`
	Name       string `json:"name"`
	ParentPath string `json:"parent_path"`
	Content    string `json:"content"`
	IsDaily    bool   `json:"is_daily"`
	SortOrder  int    `json:"sort_order"`
}

type MoveRequest struct {
	NewParentPath string `json:"new_parent_path"`
	NewName       string `json:"new_name"`
}

func buildPath(parentPath, name string) string {
	if parentPath == "/" {
		return "/" + name
	}
	return parentPath + "/" + name
}

func scanNode(rows interface{ Scan(...interface{}) error }) (*FsNode, error) {
	var n FsNode
	var created, updated string
	var isDaily int
	err := rows.Scan(&n.ID, &n.Type, &n.Name, &n.Path, &n.ParentPath, &n.Content, &isDaily, &n.SortOrder, &created, &updated)
	if err != nil {
		return nil, err
	}
	n.IsDaily = isDaily == 1
	if created != "" {
		n.CreatedAt = &created
	}
	if updated != "" {
		n.UpdatedAt = &updated
	}
	return &n, nil
}

// GetTree returns the filesystem tree structure
func GetTree(c *gin.Context) {
	log.Printf("GetTree: Fetching filesystem tree")

	parentPath := c.Query("parent_path")

	var rows *sql.Rows
	var err error

	if parentPath != "" {
		rows, err = database.DB.Query(`
			SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
			FROM fs_nodes
			WHERE parent_path = ?
			ORDER BY type DESC, sort_order ASC, name ASC
		`, parentPath)
	} else {
		rows, err = database.DB.Query(`
			SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
			FROM fs_nodes
			ORDER BY type DESC, sort_order ASC, name ASC
		`)
	}

	if err != nil {
		log.Printf("GetTree: Query failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to fetch nodes"})
		return
	}
	defer rows.Close()

	nodes := make([]FsNode, 0)
	for rows.Next() {
		n, err := scanNode(rows)
		if err != nil {
			log.Printf("GetTree: Scan failed: %v", err)
			continue
		}
		nodes = append(nodes, *n)
	}

	log.Printf("GetTree: Found %d nodes", len(nodes))
	c.JSON(200, nodes)
}

// GetNode returns a single node by path
func GetNode(c *gin.Context) {
	nodePath := c.Query("path")
	if nodePath == "" {
		c.JSON(400, gin.H{"error": "Path is required"})
		return
	}

	row := database.DB.QueryRow(`
		SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
		FROM fs_nodes
		WHERE path = ?
	`, nodePath)

	n, err := scanNode(row)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Node not found"})
		return
	}
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch node"})
		return
	}

	c.JSON(200, n)
}

// GetNodeById returns a single node by ID
func GetNodeById(c *gin.Context) {
	id := c.Param("id")

	row := database.DB.QueryRow(`
		SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
		FROM fs_nodes
		WHERE id = ?
	`, id)

	n, err := scanNode(row)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Node not found"})
		return
	}
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to fetch node"})
		return
	}

	c.JSON(200, n)
}

// CreateNode creates a new file or folder
func CreateNode(c *gin.Context) {
	var req FsNodeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	if req.Type != "folder" && req.Type != "file" {
		c.JSON(400, gin.H{"error": "Type must be 'folder' or 'file'"})
		return
	}

	if req.Name == "" {
		c.JSON(400, gin.H{"error": "Name is required"})
		return
	}

	if req.ParentPath == "" {
		req.ParentPath = "/"
	}

	// Check if parent exists (unless parent is root)
	if req.ParentPath != "/" {
		var parentExists bool
		err := database.DB.QueryRow(
			"SELECT 1 FROM fs_nodes WHERE path = ? AND type = 'folder'",
			req.ParentPath,
		).Scan(&parentExists)
		if err == sql.ErrNoRows {
			c.JSON(400, gin.H{"error": "Parent folder not found"})
			return
		}
	}

	// Build the full path
	nodePath := buildPath(req.ParentPath, req.Name)

	// Check if path already exists
	var pathExists bool
	err := database.DB.QueryRow("SELECT 1 FROM fs_nodes WHERE path = ?", nodePath).Scan(&pathExists)
	if err != sql.ErrNoRows {
		c.JSON(409, gin.H{"error": "Path already exists"})
		return
	}

	id := database.GenerateID()
	now := time.Now().Format(time.RFC3339)

	_, err = database.DB.Exec(`
		INSERT INTO fs_nodes (id, type, name, path, parent_path, content, is_daily, sort_order, created, updated)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, id, req.Type, req.Name, nodePath, req.ParentPath, req.Content, req.IsDaily, req.SortOrder, now, now)

	if err != nil {
		log.Printf("CreateNode: Insert failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to create node"})
		return
	}

	node := FsNode{
		ID:         id,
		Type:       req.Type,
		Name:       req.Name,
		Path:       nodePath,
		ParentPath: req.ParentPath,
		Content:    req.Content,
		IsDaily:    req.IsDaily,
		SortOrder:  req.SortOrder,
		CreatedAt:  &now,
		UpdatedAt:  &now,
	}

	log.Printf("CreateNode: Created %s at %s", req.Type, nodePath)
	c.JSON(201, node)
}

// UpdateNode updates an existing node
func UpdateNode(c *gin.Context) {
	id := c.Param("id")

	var req FsNodeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	// Check if node exists and get current values
	var currentType, currentName, currentContent string
	err := database.DB.QueryRow(
		"SELECT type, name, content FROM fs_nodes WHERE id = ?",
		id,
	).Scan(&currentType, &currentName, &currentContent)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Node not found"})
		return
	}

	// Determine what to update
	newName := currentName
	if req.Name != "" {
		newName = req.Name
	}

	newContent := currentContent
	if req.Content != "" || currentType == "file" {
		newContent = req.Content
	}

	now := time.Now().Format(time.RFC3339)

	_, err = database.DB.Exec(`
		UPDATE fs_nodes
		SET name = ?, content = ?, sort_order = ?, updated = ?
		WHERE id = ?
	`, newName, newContent, req.SortOrder, now, id)

	if err != nil {
		log.Printf("UpdateNode: Update failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to update node"})
		return
	}

	// Fetch updated node
	row := database.DB.QueryRow(`
		SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
		FROM fs_nodes WHERE id = ?
	`, id)

	n, _ := scanNode(row)
	c.JSON(200, n)
}

// DeleteNode deletes a node (and children if folder)
func DeleteNode(c *gin.Context) {
	id := c.Param("id")

	// Get node info
	var nodePath, nodeType string
	err := database.DB.QueryRow(
		"SELECT path, type FROM fs_nodes WHERE id = ?",
		id,
	).Scan(&nodePath, &nodeType)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Node not found"})
		return
	}

	// If it's a folder, delete all children first
	if nodeType == "folder" {
		_, err = database.DB.Exec(
			"DELETE FROM fs_nodes WHERE path LIKE ?",
			nodePath+"/%",
		)
		if err != nil {
			log.Printf("DeleteNode: Failed to delete children: %v", err)
		}
	}

	// Delete the node itself
	_, err = database.DB.Exec("DELETE FROM fs_nodes WHERE id = ?", id)
	if err != nil {
		log.Printf("DeleteNode: Delete failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to delete node"})
		return
	}

	log.Printf("DeleteNode: Deleted %s", nodePath)
	c.Status(204)
}

// MoveNode moves or renames a node
func MoveNode(c *gin.Context) {
	id := c.Param("id")

	var req MoveRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON"})
		return
	}

	// Get current node info
	var oldPath, oldName, oldParentPath, nodeType string
	err := database.DB.QueryRow(
		"SELECT path, name, parent_path, type FROM fs_nodes WHERE id = ?",
		id,
	).Scan(&oldPath, &oldName, &oldParentPath, &nodeType)
	if err == sql.ErrNoRows {
		c.JSON(404, gin.H{"error": "Node not found"})
		return
	}

	newName := req.NewName
	if newName == "" {
		newName = oldName
	}

	newParentPath := req.NewParentPath
	if newParentPath == "" {
		newParentPath = oldParentPath
	}

	newPath := buildPath(newParentPath, newName)

	// Check if new path already exists
	if newPath != oldPath {
		var pathExists bool
		err := database.DB.QueryRow("SELECT 1 FROM fs_nodes WHERE path = ?", newPath).Scan(&pathExists)
		if err != sql.ErrNoRows {
			c.JSON(409, gin.H{"error": "Destination path already exists"})
			return
		}
	}

	now := time.Now().Format(time.RFC3339)

	// Update the node
	_, err = database.DB.Exec(`
		UPDATE fs_nodes
		SET name = ?, path = ?, parent_path = ?, updated = ?
		WHERE id = ?
	`, newName, newPath, newParentPath, now, id)

	if err != nil {
		log.Printf("MoveNode: Update failed: %v", err)
		c.JSON(500, gin.H{"error": "Failed to move node"})
		return
	}

	// If it's a folder, update all children paths
	if nodeType == "folder" {
		rows, _ := database.DB.Query(
			"SELECT id, path, parent_path FROM fs_nodes WHERE path LIKE ?",
			oldPath+"/%",
		)
		if rows != nil {
			defer rows.Close()
			for rows.Next() {
				var childID, childOldPath, childOldParent string
				rows.Scan(&childID, &childOldPath, &childOldParent)

				childNewPath := strings.Replace(childOldPath, oldPath, newPath, 1)
				childNewParent := strings.Replace(childOldParent, oldPath, newPath, 1)
				if childOldParent == oldPath {
					childNewParent = newPath
				}

				database.DB.Exec(`
					UPDATE fs_nodes SET path = ?, parent_path = ?, updated = ? WHERE id = ?
				`, childNewPath, childNewParent, now, childID)
			}
		}
	}

	// Fetch updated node
	row := database.DB.QueryRow(`
		SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
		FROM fs_nodes WHERE id = ?
	`, id)

	n, _ := scanNode(row)

	log.Printf("MoveNode: Moved %s to %s", oldPath, newPath)
	c.JSON(200, n)
}

// SearchFiles searches for files containing the query
func SearchFiles(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(400, gin.H{"error": "Search query is required"})
		return
	}

	searchPattern := "%" + query + "%"

	rows, err := database.DB.Query(`
		SELECT id, type, name, path, parent_path, content, is_daily, sort_order, created, updated
		FROM fs_nodes
		WHERE type = 'file' AND (name LIKE ? OR content LIKE ?)
		ORDER BY updated DESC
	`, searchPattern, searchPattern)

	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to search files"})
		return
	}
	defer rows.Close()

	nodes := make([]FsNode, 0)
	for rows.Next() {
		n, err := scanNode(rows)
		if err != nil {
			continue
		}
		nodes = append(nodes, *n)
	}

	c.JSON(200, nodes)
}
