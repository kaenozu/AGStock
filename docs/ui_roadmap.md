# UI Modernization Roadmap: Gemini Terminal

This document outlines the plan to build the "Gemini Terminal" UI based on the provided design reference. The goal is to replace/augment the existing Streamlit interface with a high-performance, premium Next.js web application.

## 1. Vision & Tech Stack

- **Design Philosophy**: "Terminal" Aesthetic. Dark mode only, deep navy/black backgrounds, vivid purple accents (#7c3aed), subtle gradients, monolithic font for data.
- **Framework**: Next.js 14 (App Router) + TypeScript.
- **Styling**: Tailwind CSS + Shadcn/UI (for robust accessible components).
- **Charts**: Recharts (for high-performance equity curves).
- **State Management**: Zustand (lightweight client state).
- **Icons**: Lucide React.
- **Backend Bridge**: FastAPI (or Streamlit-compatible API) to serve data to the frontend.

## 2. Implementation Phases

### Phase 1: Foundation Setup
- [ ] Initialize `web-ui` directory with `create-next-app`.
- [ ] Configure Tailwind CSS with "Gemini Terminal" color palette.
    - `bg-terminal-dark` (#1a1d2e)
    - `text-terminal-neon` (#7c3aed)
    - `border-terminal-glass` (rgba(255,255,255,0.1))
- [ ] Set up Shadcn/UI (Button, Input, Select, Table, Card).

### Phase 2: App Shell & Layout
- [ ] **Sidebar Navigation**:
    - Fixed width, collapsible.
    - Tabs: "検証 (Backtest)", "抽出 (Scanner)", "Monitor".
- [ ] **Header**:
    - "TERMINAL" branding.
    - Global actions (Watchlist, Exit).
- [ ] **Main Canvas**:
    - Responsive grid layout for widgets.

### Phase 3: The "Backtest" Workspace (Screenshot Replication)
- [ ] **Control Panel (Left)**:
    - `Select`: Watchlist loader.
    - `Select`: Algorithm Strategy picker.
    - `DatePicker`: Simulation period range.
    - `ScrollArea`: Target Tickers list.
    - `Button`: "EXECUTE BACKTEST" (Gradient styling).
- [ ] **Visualizer (Top Right)**:
    - Equity Curve Chart (Line chart with gradient fill).
    - Status Overlay ("Simulating trades...").
- [ ] **Metrics & Logs (Bottom)**:
    - `Table`: Transaction Log (Ticker, Entry, Exit, PnL).
    - `Cards`: Key Metrics (Total Return, Sharpe, DD).

### Phase 4: Data Integration (Backend)
- [ ] Create API endpoints (FastAPI wrapper around existing Python logic) for:
    - `GET /api/strategies`: List available trading logic.
    - `POST /api/backtest`: Trigger extensive backtests.
    - `GET /api/market-data`: Fetch equity curves for rendering.
- [ ] Connect Next.js frontend to Python backend via `fetch` / SWR.

### Phase 5: Polish & Animations
- [ ] Add loading skeletons and progress bars (as seen in screenshot).
- [ ] Implement "Glassmorphism" effects on panels.
- [ ] Responsive adjustments for 4K/Ultrawide monitors.

## 3. Immediate Next Steps
1. Create the Next.js project structure.
2. Configure the generic "Terminal" theme in `tailwind.config.ts`.
3. Build the static "Shell" to verify the visual fidelity.
