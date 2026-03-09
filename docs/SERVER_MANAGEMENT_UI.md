# Server Management UI Implementation

## Overview
Simplified server registration by adding a dedicated UI for managing monitoring agents. Users no longer need to make API calls via curl/Postman - everything is handled through an intuitive web interface.

## Changes Made

### 1. Frontend - New Servers Page (`frontend/src/pages/ServersPage.jsx`)

**Main Features:**
- Dedicated `/servers` route for server management
- Full CRUD operations through UI
- Automatic agent configuration file generation

**Components:**

#### ServerList Table
- Displays all registered servers
- Shows: Name, Status (online/offline), Hostname, IP Address, Last Seen timestamp
- Status indicator with colored badges (green = online, red = offline)
- Delete button for each server
- Responsive table design

#### AddServerModal
- Form to register new servers
- Fields:
  - **Server Name** (required) - Display name
  - **Hostname** (optional) - FQDN or hostname
  - **IP Address** (optional) - Server IP
  - **MAC Address** (optional) - For Wake-on-LAN
  - **Poll Interval** - How often agent reports (10-3600 seconds)
- Form validation
- Error handling with user-friendly messages
- Creates server via `POST /api/v1/servers`

#### ApiKeyModal (One-Time Display)
- Shows after successful server creation
- **Warning banner** - API key only shown once
- Displays:
  - Server ID
  - API Key with copy button
  - Download `.env` file button
- **Auto-generates agent configuration file** with:
  - `DASH_API_URL` (automatically detects from window.location)
  - `DASH_API_KEY`
  - `DASH_SERVER_ID`
  - `DASH_POLL_INTERVAL`
  - `DASH_COLLECT_DOCKER=true`
  - `DASH_COLLECT_PROCESSES=true`
  - `DASH_LOG_LEVEL=INFO`
- Downloads as `agent-{server-name}.env`
- Copy to clipboard functionality

#### DeleteConfirmModal
- Confirmation dialog before deleting
- Warns about cascade deletion (metrics, containers, processes)
- Shows server name being deleted
- Prevents accidental deletions

### 2. Routing Updates (`frontend/src/App.jsx`)

**Added:**
```jsx
<Route
  path="/servers"
  element={
    <ProtectedRoute>
      <ServersPage />
    </ProtectedRoute>
  }
/>
```

- Protected route (requires authentication)
- Accessible at `/servers`

### 3. Navigation (`frontend/src/components/layout/DashboardHeader.jsx`)

**Added "Servers" Button:**
- Positioned between "Edit" and "Dark Mode" buttons
- Icon + text ("Servers" text hidden on mobile for space)
- Links to `/servers` route
- Consistent styling with other header buttons
- Server icon (database/server symbol)

### 4. Documentation (`agent/README.md`)

**Updated Quick Start Section:**
- Added "Option A: Using the Dashboard UI (Recommended)"
- Step-by-step guide for UI registration
- Emphasizes downloading the `.env` file
- Kept API option as "Option B" for advanced users

## User Flow

### Simplified Registration Process

**Before (Complex):**
1. Make API login request via curl
2. Parse JWT token from response
3. Make server registration request with token
4. Parse server ID and API key from response
5. Manually create `.env` file with correct values
6. Upload to server

**After (Simple):**
1. Click "Servers" in dashboard header
2. Click "Add Server" button
3. Fill in form (only name is required)
4. Click "Create Server"
5. Download the generated `agent.env` file
6. Upload to server at `/etc/dash-agent/agent.env`

### Complete Workflow

1. **Navigate**: User clicks "Servers" in dashboard header
2. **View**: Sees list of all registered servers with status
3. **Add**: Clicks "Add Server" button
4. **Fill Form**:
   - Enters server name (required)
   - Optionally adds hostname, IP, MAC address
   - Sets poll interval (defaults to 60 seconds)
5. **Submit**: Clicks "Create Server"
6. **API Key Modal Appears**:
   - Shows server ID
   - Shows API key (only time it's visible)
   - Provides "Copy" button for API key
   - Provides "Download agent.env File" button
7. **Download Config**: User clicks download to get pre-configured file
8. **Deploy**: User uploads `agent.env` to server and starts agent
9. **Monitor**: Server appears in list, status updates when agent starts reporting

## Technical Details

### API Integration

**Endpoints Used:**
- `GET /api/v1/servers` - List all servers
- `POST /api/v1/servers` - Create new server
- `DELETE /api/v1/servers/{id}` - Delete server

**Authentication:**
- Uses JWT token from localStorage (`access_token`)
- All requests include `Authorization: Bearer {token}` header

### Auto-Detection

**API URL:**
The generated `.env` file automatically uses `window.location.origin` to set the API URL, so it works for:
- Local development (`http://localhost:5173` → `http://localhost:8000/api/v1`)
- Production (`https://dash.example.com` → `https://dash.example.com/api/v1`)

No manual URL configuration needed!

### File Download

**Implementation:**
```javascript
const blob = new Blob([envFileContent], { type: 'text/plain' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `agent-${server.name}.env`;
a.click();
URL.revokeObjectURL(url);
```

Creates a downloadable file client-side without server roundtrip.

### Real-Time Updates

**Server List:**
- Fetches servers on page load
- Refreshes after adding a server
- Refreshes after deleting a server
- Shows online/offline status with color-coded badges
- Displays last seen timestamp

## UI/UX Features

### Responsive Design
- Mobile-friendly table (horizontal scroll on small screens)
- "Servers" text hidden on mobile (icon only)
- Modals are full-width on small screens with horizontal padding

### Dark Mode Support
- All components support light/dark themes
- Uses Tailwind dark mode classes
- Inherits theme from ThemeContext

### Loading States
- Spinner while fetching servers
- "Creating..." / "Deleting..." button states
- Disabled inputs during submission

### Empty States
- Friendly empty state when no servers registered
- Large icon + message
- "Add Your First Server" CTA button

### Error Handling
- API errors shown in red alert boxes
- Form validation errors
- Network error handling
- Graceful fallbacks

### Security
- API key only shown once (can't retrieve later)
- Yellow warning banner to emphasize saving
- Copy and download options provided immediately
- API key hidden after modal closes

## Benefits

### For Users
- ✅ No API knowledge required
- ✅ No curl/Postman needed
- ✅ Auto-generated configuration (no typos)
- ✅ Visual server status monitoring
- ✅ Easy server management (add/delete)
- ✅ One-click config file download

### For Administrators
- ✅ Reduces support requests
- ✅ Fewer configuration errors
- ✅ Faster onboarding
- ✅ Centralized server management
- ✅ Visual overview of all servers

### For Developers
- ✅ Consistent with existing UI patterns
- ✅ Reusable modal components
- ✅ Proper error handling
- ✅ Type-safe API integration

## Testing Checklist

- [ ] Navigate to `/servers` from dashboard
- [ ] View list of servers (if any exist)
- [ ] Click "Add Server"
- [ ] Fill in form and submit
- [ ] Verify API key modal appears
- [ ] Copy API key to clipboard
- [ ] Download `.env` file
- [ ] Verify file contents are correct
- [ ] Close modal
- [ ] Verify new server appears in list
- [ ] Delete a server
- [ ] Confirm deletion
- [ ] Verify server removed from list
- [ ] Test dark mode toggle
- [ ] Test on mobile viewport
- [ ] Test error states (invalid data, network errors)

## Future Enhancements

Potential improvements:
- **Edit server details** - Update name, hostname, IP after creation
- **Regenerate API key** - Allow key rotation for security
- **Agent status details** - Show version, uptime, last metrics received
- **Bulk operations** - Delete multiple servers at once
- **Server grouping** - Organize servers by location/environment
- **Quick actions** - Wake-on-LAN, restart agent, view logs
- **Setup wizard** - Step-by-step guide for first-time users
- **Agent installation script** - One-liner to install and configure
- **Server templates** - Pre-configured setups for common scenarios

## Migration Path

Existing users with API-registered servers can:
1. Navigate to new `/servers` page
2. See their existing servers in the list
3. Continue using them normally
4. Add new servers via UI going forward

No migration or data changes needed - fully backward compatible!
