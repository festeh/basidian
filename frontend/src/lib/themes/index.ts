import type { Theme, ThemeName } from '$lib/types';

export const themes: Record<ThemeName, Theme> = {
	'catppuccin-mocha': {
		name: 'catppuccin-mocha',
		displayName: 'Catppuccin Mocha',
		isDark: true,
		shikiTheme: 'catppuccin-mocha',
		colors: {
			base: '#1e1e2e',
			mantle: '#181825',
			surface: '#313244',
			overlay: '#45475a',
			text: '#cdd6f4',
			subtext: '#a6adc8',
			accent: '#89b4fa',
			secondary: '#f5c2e7',
			error: '#f38ba8',
			success: '#a6e3a1',
			codeKeyword: '#cba6f7',
			codeString: '#a6e3a1',
			codeComment: '#6c7086',
			codeNumber: '#fab387',
			codeFunction: '#89b4fa',
			codeVariable: '#f5c2e7',
			codeOperator: '#94e2d5'
		}
	},
	'catppuccin-latte': {
		name: 'catppuccin-latte',
		displayName: 'Catppuccin Latte',
		isDark: false,
		shikiTheme: 'catppuccin-latte',
		colors: {
			base: '#eff1f5',
			mantle: '#e6e9ef',
			surface: '#ccd0da',
			overlay: '#bcc0cc',
			text: '#4c4f69',
			subtext: '#6c6f85',
			accent: '#1e66f5',
			secondary: '#ea76cb',
			error: '#d20f39',
			success: '#40a02b',
			codeKeyword: '#8839ef',
			codeString: '#40a02b',
			codeComment: '#9ca0b0',
			codeNumber: '#fe640b',
			codeFunction: '#1e66f5',
			codeVariable: '#ea76cb',
			codeOperator: '#179299'
		}
	},
	nord: {
		name: 'nord',
		displayName: 'Nord',
		isDark: true,
		shikiTheme: 'nord',
		colors: {
			base: '#2e3440',
			mantle: '#272c36',
			surface: '#3b4252',
			overlay: '#434c5e',
			text: '#eceff4',
			subtext: '#d8dee9',
			accent: '#88c0d0',
			secondary: '#81a1c1',
			error: '#bf616a',
			success: '#a3be8c',
			codeKeyword: '#81a1c1',
			codeString: '#a3be8c',
			codeComment: '#616e88',
			codeNumber: '#b48ead',
			codeFunction: '#88c0d0',
			codeVariable: '#d8dee9',
			codeOperator: '#81a1c1'
		}
	},
	dracula: {
		name: 'dracula',
		displayName: 'Dracula',
		isDark: true,
		shikiTheme: 'dracula',
		colors: {
			base: '#282a36',
			mantle: '#21222c',
			surface: '#44475a',
			overlay: '#6272a4',
			text: '#f8f8f2',
			subtext: '#bfbfbf',
			accent: '#bd93f9',
			secondary: '#ff79c6',
			error: '#ff5555',
			success: '#50fa7b',
			codeKeyword: '#ff79c6',
			codeString: '#f1fa8c',
			codeComment: '#6272a4',
			codeNumber: '#bd93f9',
			codeFunction: '#50fa7b',
			codeVariable: '#f8f8f2',
			codeOperator: '#ff79c6'
		}
	},
	'gruvbox-dark': {
		name: 'gruvbox-dark',
		displayName: 'Gruvbox Dark',
		isDark: true,
		shikiTheme: 'vitesse-dark',
		colors: {
			base: '#282828',
			mantle: '#1d2021',
			surface: '#3c3836',
			overlay: '#504945',
			text: '#ebdbb2',
			subtext: '#a89984',
			accent: '#fe8019',
			secondary: '#fabd2f',
			error: '#fb4934',
			success: '#b8bb26',
			codeKeyword: '#fb4934',
			codeString: '#b8bb26',
			codeComment: '#928374',
			codeNumber: '#d3869b',
			codeFunction: '#fabd2f',
			codeVariable: '#83a598',
			codeOperator: '#8ec07c'
		}
	}
};

export const themeList = Object.values(themes);
