package database

import (
	"database/sql"
	"log"

	_ "modernc.org/sqlite"
)

var DB *sql.DB

// Init opens the SQLite database and ensures tables exist
func Init(dbPath string) error {
	var err error
	DB, err = sql.Open("sqlite", dbPath)
	if err != nil {
		return err
	}

	// Test connection
	if err := DB.Ping(); err != nil {
		return err
	}

	// Run migrations to ensure tables exist
	if err := runMigrations(); err != nil {
		return err
	}

	log.Printf("Database initialized: %s", dbPath)
	return nil
}

// Close closes the database connection
func Close() {
	if DB != nil {
		DB.Close()
	}
}

func runMigrations() error {
	// Create notes table if not exists
	_, err := DB.Exec(`
		CREATE TABLE IF NOT EXISTS notes (
			id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
			title TEXT DEFAULT '' NOT NULL,
			content TEXT DEFAULT '' NOT NULL,
			date TEXT DEFAULT '' NOT NULL,
			created TEXT DEFAULT '' NOT NULL,
			updated TEXT DEFAULT '' NOT NULL
		)
	`)
	if err != nil {
		return err
	}

	// Create fs_nodes table if not exists
	_, err = DB.Exec(`
		CREATE TABLE IF NOT EXISTS fs_nodes (
			id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
			type TEXT DEFAULT '' NOT NULL,
			name TEXT DEFAULT '' NOT NULL,
			path TEXT DEFAULT '' NOT NULL,
			parent_path TEXT DEFAULT '' NOT NULL,
			content TEXT DEFAULT '' NOT NULL,
			is_daily BOOLEAN DEFAULT FALSE NOT NULL,
			sort_order NUMERIC DEFAULT 0 NOT NULL,
			created TEXT DEFAULT '' NOT NULL,
			updated TEXT DEFAULT '' NOT NULL
		)
	`)
	if err != nil {
		return err
	}

	// Create indexes
	_, _ = DB.Exec(`CREATE UNIQUE INDEX IF NOT EXISTS idx_fs_nodes_path ON fs_nodes (path)`)
	_, _ = DB.Exec(`CREATE INDEX IF NOT EXISTS idx_fs_nodes_parent_path ON fs_nodes (parent_path)`)
	_, _ = DB.Exec(`CREATE INDEX IF NOT EXISTS idx_fs_nodes_type ON fs_nodes (type)`)
	_, _ = DB.Exec(`CREATE INDEX IF NOT EXISTS idx_notes_date ON notes (date)`)

	return nil
}

// GenerateID creates a random ID similar to PocketBase format
func GenerateID() string {
	var id string
	row := DB.QueryRow("SELECT lower(hex(randomblob(8)))")
	row.Scan(&id)
	return id
}
