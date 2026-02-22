# Middle Over Strike Rate Optimizer - Frontend

## Overview

The frontend is a **React-based web application** with a modern, responsive UI that provides a tactical dashboard for cricket match analysis. It allows users to input match scenarios and receive AI-powered batting order recommendations from the backend ML model.

## Technology Stack

- **Framework**: React 19.2.0
- **Build Tool**: Vite 7.3.1
- **Styling**: Tailwind CSS 3.4.19
- **Language**: JavaScript/TypeScript
- **UI Components**: Custom React components with Tailwind styling
- **Code Quality**: ESLint with React plugins

## Project Structure

```
frontend/
├── index.html                          # HTML entry point
├── package.json                        # Dependencies and scripts
├── vite.config.js                      # Vite configuration
├── tailwind.config.js                  # Tailwind CSS configuration
├── eslint.config.js                    # ESLint configuration
├── src/
│   ├── main.jsx                        # React root entry
│   ├── App.jsx                         # Main app component
│   ├── App.css                         # Global styles
│   ├── index.css                       # Tailwind imports
│   ├── components/
│   │   └── TacticalDashboard.tsx       # Main dashboard component
│   ├── assets/                         # Static assets (images, icons)
│   └── data/                           # Static data files
│       ├── index.js                    # Barrel export
│       ├── venueData.js                # Venue configurations
│       ├── bowlerGroups.js             # Bowler types
│       └── batterData.js               # Player database with strike rates
└── public/                             # Public static files
```

## Setup & Installation

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn

### Install Dependencies

```bash
cd frontend
npm install
```

## Development

### Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173` with hot module reloading enabled.

### Build for Production

```bash
npm run build
```

Creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

### Linting

```bash
npm run lint
```

Runs ESLint to check code quality and style compliance.

## Key Features

### 1. **Tactical Dashboard**

The main component (`TacticalDashboard.tsx`) provides:

- Real-time match scenario configuration
- Dynamic run rate calculation
- One-click optimization requests
- Results visualization in an interactive ranked table
- Player strike rate tracking

### 2. **Input Parameters**

#### Match Context

- **Over**: Current over number (7-15)
- **Wickets Lost**: Cumulative wickets (0-9)
- **Current Score**: Total runs scored
- **Inning**: Inning number (1st or 2nd)
- **Run Rate**: Auto-calculated from score and over

#### Tactical Inputs

- **Venue**: Dropdown selection (Neutral, Home, Away, etc.)
- **Bowler Type**: Classification (Pacer, Spinner, All-Rounder)
- **Available Batters**: Multi-select from player pool with strike rates

### 3. **Results Display**

The dashboard presents optimization results in a ranked table:

| Column                 | Description                                 |
| ---------------------- | ------------------------------------------- |
| Rank                   | Recommendation priority (#1 is best)        |
| Batter                 | Player name and image                       |
| Tactical Utility Score | Overall suitability score (higher = better) |
| Boundary Prob          | Probability of hitting boundaries (%)       |
| Strike Rotation        | Probability of rotating strike (%)          |
| Pressure Risk          | Probability of facing pressure (%)          |

**Visual Indicators**:

- Top-ranked batter highlighted with blue background
- Player images and stats for quick identification
- Color-coded probability indicators
- Responsive table layout for mobile devices

## Component Architecture

### TacticalDashboard Component

**State Management**:

```tsx
interface BatterSelection {
  name: string; // Player's unique identifier
  sr: float; // Recent strike rate (last 5 games)
}

// Match configuration
const [over, setOver] = useState<number>(10);
const [wickets, setWickets] = useState<number>(3);
const [score, setScore] = useState<number>(75);
const [inning, setInning] = useState<number>(1);

// Tactical selection with strike rates
const [selectedBatters, setSelectedBatters] = useState<BatterSelection[]>([
  { name: "KIC Asalanka", sr: 120.0 },
  { name: "MD Shanaka", sr: 115.5 },
]);

// Results
const [results, setResults] = useState<PredictionResult[]>([]);
const [isLoading, setIsLoading] = useState<boolean>(false);
```

**Key Functions**:

1. **toggleBatter()**
   - Adds/removes batters from selection
   - Extracts strike rate from batter database
   - Updates state with `{name, sr}` objects

2. **handleOptimize()**
   - Constructs request payload with batter objects
   - Sends POST request to `/api/optimize`
   - Displays loading state during processing
   - Updates results on success

3. **Auto-calculated Metrics**
   - Run Rate: `score / over`
   - Venue Type: Lookup from venue selection
   - Feature alignment with backend expectations

## Data Files

### batterData

```javascript
[
  {
    unique_name: "KIC Asalanka",
    common_name: "Charith Asalanka",
    country: "Sri Lanka",
    img_url: "...",
    sr: 120.5                          // Strike rate for selection
  },
  ...
]
```

### venueData

```javascript
[
  { name: "MCG", venueType: "Neutral" },
  { name: "Eden Gardens", venueType: "Home" },
  ...
]
```

### bowlerGroups

```javascript
[{ type: "Pacer" }, { type: "Spinner" }, { type: "All-Rounder" }];
```

## API Integration

### Backend Connection

The frontend sends requests in this format:

```javascript
const payload = {
  Over: 10,
  Cumulative_Wickets: 3,
  Current_Run_Rate: 7.5,
  Inning: 1,
  Venue_Type: "Neutral",
  Bowler_Group: "Pacer",
  available_batters: [
    { name: "KIC Asalanka", sr: 120.0 },
    { name: "MD Shanaka", sr: 115.5 },
  ],
};

const response = await fetch("http://localhost:8000/api/optimize", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```

### Error Handling

- Network errors: User-friendly alert messages
- Invalid responses: Validation and fallback UI
- Loading states: Visual feedback during processing

### CORS Requirements

- Backend must have CORS enabled for `http://localhost:5173` (dev)
- Production URLs must be added to backend's `allow_origins`

## Styling

### Tailwind CSS

The application uses Tailwind CSS utility classes for styling:

- **Dark theme**: Slate color palette (slate-50 to slate-950)
- **Accent colors**: Blue for highlights and interactions
- **Responsive design**: Mobile-first approach with breakpoints

### Key Classes

- `.bg-slate-900`: Dark background
- `.text-slate-300`: Light text on dark background
- `.border-blue-500`: Blue accents
- `.rounded-lg`: Rounded corners
- `.shadow-lg`: Elevation effects
- `.animate-spin`: Loading spinner

## Browser Support

- **Chrome/Edge**: Latest 2 versions
- **Firefox**: Latest 2 versions
- **Safari**: Latest 2 versions
- **Mobile Browsers**: iOS Safari 12+, Chrome Android latest

## Performance Optimization

### Techniques Used

- **Memoization**: `useMemo` for expensive calculations
- **Conditional Rendering**: Display only necessary UI elements
- **Lazy Loading**: Images load as needed
- **Code Splitting**: Vite handles automatic code splitting

### Bundle Size

- Production build: ~150KB (gzipped)
- CSS: ~20KB (Tailwind purged)
- JavaScript: ~80KB (React + app logic)

## Development Guidelines

### Component Creation

1. Use functional components with hooks
2. Employ `use*` hooks for state and effects
3. Memoize expensive calculations with `useMemo`
4. Type components with TypeScript (`.tsx`)

### State Management

- Local state for component-specific data (match config, batter selection)
- Props for parent-child communication
- Batter selection now requires both name and strike rate

### Styling

- Use Tailwind classes for styling
- Create custom classes in `index.css` for complex styles
- Follow dark theme consistency
- Test responsive behavior on mobile devices

## Deployment

### Production Build

```bash
npm run build
```

### Serving the Build

The `dist/` folder contains production-ready files:

**Using Node.js/Express**:

```javascript
app.use(express.static("dist"));
app.get("*", (req, res) => res.sendFile("dist/index.html"));
```

**Using Nginx**:

```nginx
location / {
  root /var/www/frontend;
  try_files $uri /index.html;
}
```

**Using Vercel/Netlify**:
Simply connect your Git repository for automatic deployments.

### Environment Variables

Create a `.env` file for environment-specific settings:

```
VITE_API_URL=http://localhost:8000
```

Access in code:

```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Troubleshooting

| Issue                               | Solution                                                     |
| ----------------------------------- | ------------------------------------------------------------ |
| Blank white screen                  | Check browser console for errors, verify Vite is running     |
| API calls fail                      | Ensure backend is running on port 8000, check CORS settings  |
| Styling looks wrong                 | Clear cache, restart dev server, verify Tailwind config      |
| Images not loading                  | Check image paths in batterData, verify assets folder exists |
| Hot reload not working              | Restart dev server, check Vite config                        |
| "Please select at least one batter" | Add batters to selection using the dugout panel              |

## Future Enhancements

- **Authentication**: Add user login/registration
- **Match History**: Save and load previous match scenarios
- **Player Profiles**: Detailed player statistics and trends
- **Advanced Analytics**: Charts and statistical breakdowns
- **Team Management**: Save favorite player combinations
- **Export Reports**: Download optimization results as PDF
- **Real-Time Updates**: WebSocket integration for live match data
- **Mobile App**: Native iOS/Android applications
- **Dynamic Strike Rates**: Fetch live player form data from APIs

## Security Considerations

- **Input Validation**: All user inputs are validated before API calls
- **API Communication**: Use HTTPS in production
- **CORS**: Restrict to trusted domains only
- **Rate Limiting**: Implement on backend for production
- **Data Privacy**: No personal data is stored locally

## Contributing

### Code Style

- Follow ESLint rules (run `npm run lint`)
- Use meaningful variable and function names
- Add comments for complex logic
- Keep components focused and reusable

## License

This project is part of the Middle Over Strike Rate Optimizer initiative.

## Support

For issues, feature requests, or questions:

1. Check existing documentation
2. Review the troubleshooting section
3. Contact the development team
