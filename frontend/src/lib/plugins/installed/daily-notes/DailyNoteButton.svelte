<script lang="ts">
	import { openOrCreateDaily, getDailyNotesForMonth } from './index';
	import { rootNodes } from '$lib/stores/filesystem';

	let showCalendar = $state(false);
	let currentDate = $state(new Date());

	const year = $derived(currentDate.getFullYear());
	const month = $derived(currentDate.getMonth());

	const monthName = $derived(
		currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })
	);

	const existingDays = $derived.by(() => {
		void $rootNodes;
		return getDailyNotesForMonth(year, month);
	});

	const calendarDays = $derived.by(() => {
		const firstDay = new Date(year, month, 1);
		const lastDay = new Date(year, month + 1, 0);
		const startPadding = firstDay.getDay();
		const totalDays = lastDay.getDate();

		const days: (number | null)[] = [];
		for (let i = 0; i < startPadding; i++) {
			days.push(null);
		}
		for (let i = 1; i <= totalDays; i++) {
			days.push(i);
		}
		return days;
	});

	const today = new Date();
	const isCurrentMonth = $derived(
		today.getFullYear() === year && today.getMonth() === month
	);
	const todayDate = today.getDate();

	async function handleTodayClick() {
		await openOrCreateDaily(new Date());
	}

	function toggleCalendar() {
		showCalendar = !showCalendar;
		if (showCalendar) {
			currentDate = new Date();
		}
	}

	function prevMonth() {
		currentDate = new Date(year, month - 1, 1);
	}

	function nextMonth() {
		currentDate = new Date(year, month + 1, 1);
	}

	async function selectDay(day: number) {
		const date = new Date(year, month, day);
		await openOrCreateDaily(date);
		showCalendar = false;
	}

	function handleClickOutside(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (!target.closest('.daily-notes-container')) {
			showCalendar = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="daily-notes-container">
	<button class="today-btn" onclick={handleTodayClick} title="Open today's note">
		<span class="today-icon">T</span>
	</button>
	<button class="calendar-btn" onclick={toggleCalendar} title="Open calendar">
		<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
			<path
				d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"
			/>
		</svg>
	</button>

	{#if showCalendar}
		<div class="calendar-popup">
			<div class="calendar-header">
				<button class="nav-btn" onclick={prevMonth} title="Previous month">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
						<path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
					</svg>
				</button>
				<span class="month-label">{monthName}</span>
				<button class="nav-btn" onclick={nextMonth} title="Next month">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
						<path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
					</svg>
				</button>
			</div>

			<div class="weekdays">
				<span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
			</div>

			<div class="days">
				{#each calendarDays as day}
					{#if day === null}
						<span class="day empty"></span>
					{:else}
						<button
							class="day"
							class:today={isCurrentMonth && day === todayDate}
							class:has-note={existingDays.has(day)}
							onclick={() => selectDay(day)}
						>
							{day}
						</button>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.daily-notes-container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.today-btn {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		background: transparent;
		border: none;
		border-radius: 6px;
		color: var(--color-subtext);
		cursor: pointer;
		transition: all 0.15s;
	}

	.today-btn:hover {
		background: var(--color-surface);
		color: var(--color-text);
	}

	.today-icon {
		font-size: 14px;
		font-weight: 600;
	}

	.calendar-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		background: transparent;
		border: none;
		border-radius: 6px;
		color: var(--color-subtext);
		cursor: pointer;
		transition: all 0.15s;
	}

	.calendar-btn:hover {
		background: var(--color-surface);
		color: var(--color-text);
	}

	.calendar-popup {
		position: absolute;
		top: 100%;
		left: 0;
		margin-top: 8px;
		padding: 12px;
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
		z-index: 1000;
		min-width: 220px;
	}

	.calendar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 8px;
	}

	.nav-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		background: transparent;
		border: none;
		border-radius: 4px;
		color: var(--color-subtext);
		cursor: pointer;
	}

	.nav-btn:hover {
		background: var(--color-overlay);
		color: var(--color-text);
	}

	.month-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--color-text);
	}

	.weekdays {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
		margin-bottom: 4px;
	}

	.weekdays span {
		text-align: center;
		font-size: 9px;
		color: var(--color-subtext);
		padding: 2px 0;
	}

	.days {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
	}

	.day {
		aspect-ratio: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 10px;
		background: transparent;
		border: none;
		border-radius: 4px;
		color: var(--color-text);
		cursor: pointer;
		position: relative;
	}

	.day:not(.empty):hover {
		background: var(--color-overlay);
	}

	.day.empty {
		cursor: default;
	}

	.day.today {
		background: var(--color-accent);
		color: var(--color-base);
		font-weight: 600;
	}

	.day.today:hover {
		filter: brightness(1.1);
	}

	.day.has-note:not(.today)::after {
		content: '';
		position: absolute;
		bottom: 1px;
		width: 3px;
		height: 3px;
		border-radius: 50%;
		background: var(--color-accent);
	}
</style>
