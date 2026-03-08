# Installing GSAP for Professional Animations

To get the Leo9 Studio-quality animations, you need to install GSAP:

```bash
cd apps/web
npm install gsap
```

After installation, restart the marketing dev server:

```bash
npm run dev:marketing
```

The animations will automatically work once GSAP is installed. The components are designed to work conditionally - they'll use GSAP if available, or fall back to CSS animations if not.
