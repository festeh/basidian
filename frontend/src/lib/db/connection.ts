import Database from '@tauri-apps/plugin-sql';
import { CREATE_TABLES, SCHEMA_VERSION } from './schema';

let db: Database | null = null;

export async function getDb(): Promise<Database> {
	if (db) return db;

	db = await Database.load('sqlite:basidian-local.db');
	await db.execute('PRAGMA foreign_keys = ON');
	await runMigrations(db);
	return db;
}

async function runMigrations(conn: Database): Promise<void> {
	// sync_meta must exist before we can check schema version
	await conn.execute(`
		CREATE TABLE IF NOT EXISTS sync_meta (
			key   TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)
	`);

	const rows = await conn.select<{ value: string }[]>(
		"SELECT value FROM sync_meta WHERE key = 'schema_version'"
	);

	if (rows.length === 0) {
		for (const stmt of CREATE_TABLES) {
			await conn.execute(stmt);
		}
		await conn.execute(
			"INSERT INTO sync_meta (key, value) VALUES ('schema_version', $1)",
			[String(SCHEMA_VERSION)]
		);
		return;
	}

	const current = parseInt(rows[0].value, 10);
	if (current < SCHEMA_VERSION) {
		// Future migrations go here
	}
}

export async function closeDb(): Promise<void> {
	if (db) {
		await db.close();
		db = null;
	}
}
