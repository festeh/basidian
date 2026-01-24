import { writeTextFile, mkdir, exists, BaseDirectory } from '@tauri-apps/plugin-fs';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
	level: LogLevel;
	module: string;
	message: string;
	data?: unknown;
	timestamp: Date;
}

const LEVEL_PRIORITY: Record<LogLevel, number> = {
	debug: 0,
	info: 1,
	warn: 2,
	error: 3
};

const LEVEL_STYLES: Record<LogLevel, string> = {
	debug: 'color: #888',
	info: 'color: #89b4fa',
	warn: 'color: #fab387',
	error: 'color: #f38ba8; font-weight: bold'
};

class Logger {
	private minLevel: LogLevel = 'debug';
	private enabled = true;
	private logQueue: string[] = [];
	private flushTimeout: ReturnType<typeof setTimeout> | null = null;
	private logDirReady = false;

	private get isTauri(): boolean {
		return typeof window !== 'undefined' && '__TAURI__' in window;
	}

	setLevel(level: LogLevel) {
		this.minLevel = level;
	}

	enable() {
		this.enabled = true;
	}

	disable() {
		this.enabled = false;
	}

	private shouldLog(level: LogLevel): boolean {
		return this.enabled && LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[this.minLevel];
	}

	private formatModule(module: string): string {
		return `[${module}]`;
	}

	private async ensureLogDir() {
		if (!this.isTauri || this.logDirReady) return;
		try {
			const dirExists = await exists('basidian', { baseDir: BaseDirectory.Temp });
			if (!dirExists) {
				await mkdir('basidian', { baseDir: BaseDirectory.Temp, recursive: true });
			}
			this.logDirReady = true;
		} catch {
			// Ignore errors - file logging will silently fail
		}
	}

	private async flushToFile() {
		if (this.logQueue.length === 0 || !this.isTauri) return;

		const lines = this.logQueue.join('');
		this.logQueue = [];

		try {
			await this.ensureLogDir();
			await writeTextFile('basidian/frontend.log', lines, {
				baseDir: BaseDirectory.Temp,
				append: true
			});
		} catch {
			// Ignore errors - console logging still works
		}
	}

	private queueLogEntry(level: LogLevel, module: string, message: string, data?: unknown) {
		const entry: Record<string, unknown> = {
			ts: new Date().toISOString(),
			level,
			module,
			msg: message
		};
		if (data !== undefined) {
			entry.data = data;
		}
		this.logQueue.push(JSON.stringify(entry) + '\n');

		// Flush immediately (no batching)
		this.flushToFile();
	}

	private log(level: LogLevel, module: string, message: string, data?: unknown) {
		if (!this.shouldLog(level)) return;

		const entry: LogEntry = {
			level,
			module,
			message,
			data,
			timestamp: new Date()
		};

		const prefix = `%c${level.toUpperCase().padEnd(5)} ${this.formatModule(module)}`;
		const style = LEVEL_STYLES[level];

		if (data !== undefined) {
			console[level === 'debug' ? 'log' : level](prefix, style, message, data);
		} else {
			console[level === 'debug' ? 'log' : level](prefix, style, message);
		}

		// Queue for file output
		this.queueLogEntry(level, module, message, data);

		return entry;
	}

	createLogger(module: string) {
		return {
			debug: (message: string, data?: unknown) => this.log('debug', module, message, data),
			info: (message: string, data?: unknown) => this.log('info', module, message, data),
			warn: (message: string, data?: unknown) => this.log('warn', module, message, data),
			error: (message: string, data?: unknown) => this.log('error', module, message, data)
		};
	}
}

export const logger = new Logger();
export const createLogger = (module: string) => logger.createLogger(module);
