import { getInsets, type Insets } from 'tauri-plugin-safe-area-insets';

/**
 * Applies safe area insets as CSS custom properties on the document root.
 * Falls back gracefully on non-mobile platforms.
 */
export async function applySafeAreaInsets(): Promise<void> {
	try {
		const insets: Insets = await getInsets();
		const root = document.documentElement;

		root.style.setProperty('--safe-area-inset-top', `${insets.top}px`);
		root.style.setProperty('--safe-area-inset-right', `${insets.right}px`);
		root.style.setProperty('--safe-area-inset-bottom', `${insets.bottom}px`);
		root.style.setProperty('--safe-area-inset-left', `${insets.left}px`);

		console.log('Safe area insets applied:', insets);
	} catch (error) {
		// Not on mobile or plugin not available - CSS env() fallback will be used
		console.log('Safe area insets plugin not available, using CSS fallback');
	}
}
