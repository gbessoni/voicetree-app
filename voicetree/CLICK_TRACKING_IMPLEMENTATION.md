# Link Click Tracking Implementation

## Overview
Complete end-to-end link click tracking system with analytics dashboard display.

## What Was Implemented

### 1. Database Model Updates (models.py)
- Added `referrer` field to LinkClick model to track where clicks came from
- Added `user_agent` field to LinkClick model to track browser/device info
- Added relationship to Link model for easier querying

### 2. Backend API (app.py)

#### New/Updated Endpoints:
- **POST `/api/clicks/{username}/{link_id}`** - Track link clicks
  - Captures timestamp automatically
  - Extracts referrer from request headers
  - Extracts user agent from request headers
  - Increments Link.click_count
  - Increments User.total_link_clicks
  - Creates LinkClick record with all data

- **GET `/api/admin/{username}/recent-clicks`** - Get recent clicks for analytics
  - Returns last 20 clicks by default (configurable via `limit` param)
  - Includes link title, timestamp, referrer, and user agent
  - Ordered by most recent first

### 3. Frontend Profile Page (profile.html)

#### Click Tracking Before Link Opening:
```javascript
async function openLink(event, url, linkId) {
    // Track click BEFORE opening URL
    await fetch(`/api/clicks/${username}/${linkId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    
    // Then open link in new tab
    window.open(url, '_blank', 'noopener,noreferrer');
}
```

- Click tracking happens **before** opening the URL
- Uses async/await to ensure tracking completes
- Opens link in new tab after tracking
- Includes timestamp and referrer automatically from browser

### 4. Dashboard Analytics (dashboard.html)

#### Recent Clicks Table:
- Shows last 20 link clicks in real-time
- Displays:
  - Link title
  - Click timestamp (localized)
  - Referrer source (direct, website URL, etc.)
- Auto-loads when viewing Analytics tab
- Clean UI with empty state

#### Existing Analytics Enhanced:
- "Link Clicks by Link" bar chart now shows accurate data
- Total clicks stat is updated in real-time
- All analytics sync with new tracking system

## How It Works

### User Journey:
1. **Visitor lands on profile** → Profile view is tracked
2. **Visitor clicks a link** → Click tracking fires:
   - POST request sent to `/api/clicks/{username}/{link_id}`
   - Referrer captured (e.g., "https://twitter.com/post" or "direct")
   - User agent captured (browser/device info)
   - Link counter incremented
   - User total clicks incremented
   - LinkClick record created in database
3. **Link opens** → Visitor navigated to destination in new tab
4. **Dashboard updates** → Owner sees click in analytics immediately

### Data Flow:
```
Profile Page → Click Event → API Endpoint → Database Update → Analytics Display
     ↓                            ↓                ↓                  ↓
  Browser              /api/clicks/{}/{}      LinkClick        Dashboard
                        + referrer             + Link           Recent Clicks
                        + user_agent           + User           Table & Charts
                        + timestamp            counters
```

## Testing

### To Test Click Tracking:

1. **Start the server:**
   ```bash
   cd voicetree/backend
   python app.py
   ```

2. **Create a test user (if needed):**
   - Visit http://localhost:8000/signup
   - Create a user with links

3. **Test clicking links:**
   - Visit the published profile: `http://localhost:8000/{username}`
   - Click on any link
   - Check browser console for tracking confirmation
   - Verify link opens in new tab

4. **View analytics:**
   - Visit dashboard: `http://localhost:8000/dashboard/{username}`
   - Go to Analytics tab
   - Check "Recent Link Clicks" table
   - Verify click appears with:
     - Link title
     - Timestamp
     - Referrer

5. **Test different referrers:**
   - Open profile from different sources:
     - Direct (type URL)
     - From another local page
     - From external link
   - Each should show different referrer in analytics

### Expected Behavior:
- ✅ Click tracked before link opens
- ✅ Link opens in new tab immediately after tracking
- ✅ Dashboard shows click in real-time
- ✅ Click count increments on links table
- ✅ Total clicks stat updates
- ✅ Referrer properly categorized (Direct, Social, Other)

## Database Schema

```sql
CREATE TABLE link_clicks (
    id INTEGER PRIMARY KEY,
    link_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    click_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    referrer VARCHAR(500),
    user_agent VARCHAR(500),
    FOREIGN KEY (link_id) REFERENCES links(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## API Response Examples

### Track Click Response:
```json
{
    "message": "Click tracked",
    "link_id": 123
}
```

### Recent Clicks Response:
```json
[
    {
        "id": 1,
        "link_title": "My YouTube Channel",
        "link_url": "https://youtube.com/@example",
        "click_date": "2025-10-30T11:14:00",
        "referrer": "https://twitter.com/post/123",
        "user_agent": "Mozilla/5.0..."
    },
    {
        "id": 2,
        "link_title": "Portfolio Website",
        "link_url": "https://example.com",
        "click_date": "2025-10-30T10:30:00",
        "referrer": "direct",
        "user_agent": "Mozilla/5.0..."
    }
]
```

## Features

### ✅ Implemented:
- [x] Click tracking before URL opening
- [x] Timestamp capture
- [x] Referrer tracking
- [x] User agent tracking
- [x] Link counter increments
- [x] User total clicks increments
- [x] Recent clicks table in dashboard
- [x] Link clicks by link bar chart
- [x] Empty state handling
- [x] Real-time updates

### Analytics Dashboard Shows:
- Total link clicks (all-time)
- Link clicks per link (bar chart)
- Recent 20 clicks (table with details)
- Traffic sources (pie chart - includes click referrers)
- Conversion rate (views to clicks)

## Notes

- Click tracking is non-blocking - if it fails, link still opens
- All timestamps are in ISO format with timezone
- Referrer defaults to "direct" if not available
- User agent helps understand device/browser usage
- Database stores full referrer URL for detailed analytics
- Frontend displays shortened referrer (50 chars) for readability

## Future Enhancements (Optional)

- Geographic location tracking
- Device type categorization (mobile/desktop/tablet)
- Click heatmap by time of day
- A/B testing for link positions
- Export analytics to CSV
- Real-time dashboard updates via WebSocket
- Click fraud detection
