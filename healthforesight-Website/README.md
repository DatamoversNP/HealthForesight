# HealthForesight Marketing Website

Standalone marketing website for HealthForesight - Decision Intelligence for Utilization Policy Impact.

## 🚀 Quick Start

### Development

```bash
npm install
npm run dev
```

Open [http://localhost:3052](http://localhost:3052)

### Build

```bash
npm run build
```

### Deploy

#### Vercel (Recommended)

```bash
npx vercel --prod
```

Or connect your GitHub repository to Vercel for automatic deployments.

## 📁 Project Structure

```
healthforesight-Website/
├── src/
│   ├── pages/          # Marketing pages
│   ├── components/     # Reusable components
│   ├── theme/          # Theme configuration
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── index.html
├── vite.config.ts
├── package.json
└── vercel.json
```

## 🔧 Configuration

- **Vite**: Modern build tool
- **React 18**: UI framework
- **Material-UI**: Component library
- **React Router**: Client-side routing
- **GSAP**: Animations

## 📦 Dependencies

All dependencies are self-contained in this folder. No dependencies on the core application codebase.

## 🌐 Deployment

The website is configured for deployment on:
- **Vercel** (recommended) - See `vercel.json`
- **Netlify** - Compatible with Vercel config
- **Any static hosting** - Build output in `dist/`

## 📝 License

Proprietary - HealthForesight
