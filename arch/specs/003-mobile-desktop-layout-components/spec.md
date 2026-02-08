# Mobile and Desktop Layout Components

## What Users Can Do

1. **Use the app on a desktop with a multi-pane layout**

   - **Scenario: Normal desktop use**
     - **Given:** App is built with `VITE_PLATFORM=desktop`
     - **When:** User opens the app
     - **Then:** Sidebar and editor show side by side, topbar has window controls, status bar is visible

   - **Scenario: Toggle sidebar**
     - **When:** User clicks the sidebar toggle
     - **Then:** Sidebar collapses or expands without leaving the current view

2. **Use the app on a mobile device with a single-pane layout**

   - **Scenario: Open the app on mobile**
     - **Given:** App is built with `VITE_PLATFORM=mobile`
     - **When:** User opens the app
     - **Then:** Only one pane is visible at a time (file list or editor, not both)

   - **Scenario: Open the sidebar via hamburger menu**
     - **Given:** User is viewing the editor
     - **When:** User taps the hamburger menu icon in the topbar
     - **Then:** Sidebar slides in as an overlay showing the file list

   - **Scenario: Navigate from file list to editor**
     - **Given:** Sidebar is open
     - **When:** User taps a file
     - **Then:** Editor opens full-screen, sidebar closes

   - **Scenario: Close the sidebar**
     - **Given:** Sidebar is open as an overlay
     - **When:** User taps outside the sidebar or taps the hamburger icon again
     - **Then:** Sidebar closes

3. **See window controls only on desktop**

   - **Scenario: Desktop**
     - **When:** App runs on desktop
     - **Then:** Minimize, maximize, and close buttons appear in the topbar

   - **Scenario: Mobile**
     - **When:** App runs on a mobile device
     - **Then:** Window controls are hidden; the OS handles window management

4. **Use plugins on both layouts**

   - **Scenario: Open a plugin panel on desktop**
     - **When:** User opens a plugin panel (like AI Chat)
     - **Then:** Panel appears alongside the editor

   - **Scenario: Open a plugin panel on mobile**
     - **When:** User opens a plugin panel
     - **Then:** Panel takes the full screen, with a way to go back

## Requirements

- [ ] Mobile vs desktop is detected via `VITE_PLATFORM` env var set at build time (already implemented)
- [ ] Desktop layout shows sidebar and editor side by side (current behavior, unchanged)
- [ ] Desktop window resizing does not trigger mobile layout
- [ ] Mobile layout shows one pane at a time (editor full-screen by default)
- [ ] Mobile topbar has a hamburger menu icon to open the sidebar
- [ ] Mobile sidebar opens as a slide-in overlay on top of the editor
- [ ] Tapping a file in the mobile sidebar closes the sidebar and opens the file
- [ ] Tapping outside the sidebar or the hamburger icon closes the sidebar
- [ ] Window controls (minimize, maximize, close) are hidden on mobile
- [ ] Safe area insets work on both layouts (already partially done)
- [ ] Plugin panels open full-screen on mobile
- [ ] Status bar is visible on both layouts
- [ ] Touch interactions (long-press context menu) continue to work on mobile
