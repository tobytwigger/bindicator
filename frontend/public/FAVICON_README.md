# Bindicator Favicon

A colorful bin-themed favicon featuring multiple colored bins (blue, green, yellow/orange, and red) on a dark circular background.

## Files

- `favicon.svg` - Source SVG file (64x64)
- `favicon.ico` - Standard ICO format (32x32)
- `favicon-16x16.png` - 16x16 PNG
- `favicon-32x32.png` - 32x32 PNG
- `favicon-48x48.png` - 48x48 PNG
- `apple-touch-icon.png` - Apple touch icon (180x180)
- `android-chrome-192x192.png` - Android icon (192x192)
- `android-chrome-512x512.png` - Android icon (512x512)
- `site.webmanifest` - Web app manifest file

## Generation

### Method 1: Browser-based (Recommended)

1. Open `generate-favicons.html` in your browser
2. The page will auto-generate all favicon sizes
3. Click "Download All" to download all files
4. Save the files to the `public/` directory

### Method 2: Node.js Script

```bash
npm run generate:favicons
```

Note: This requires the `sharp` package and may have compatibility issues with SVG rendering.

### Method 3: Manual

Use an online converter like:
- https://realfavicongenerator.net/
- https://favicon.io/
- https://convertio.co/svg-png/

Upload `favicon.svg` and generate the required sizes.

## Colors

- Blue bin: #3b82f6
- Green bin: #10b981  
- Yellow/Orange bin: #f59e0b
- Red bin: #ef4444
- Background: #1e293b

## Integration

The favicon is automatically configured in `nuxt.config.ts` with all required meta tags and links.
