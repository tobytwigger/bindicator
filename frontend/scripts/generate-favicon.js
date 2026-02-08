#!/usr/bin/env node
/**
 * Generate favicon files from SVG source.
 * Creates .ico-compatible PNG and various PNG sizes for different platforms.
 */

import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.join(__dirname, '..', 'public');
const svgFile = path.join(publicDir, 'favicon.svg');

// Define sizes to generate
const sizes = [
  { name: 'favicon-16x16.png', size: 16 },
  { name: 'favicon-32x32.png', size: 32 },
  { name: 'favicon-48x48.png', size: 48 },
  { name: 'favicon.ico', size: 32 }, // Standard favicon.ico size
  { name: 'apple-touch-icon.png', size: 180 },
  { name: 'android-chrome-192x192.png', size: 192 },
  { name: 'android-chrome-512x512.png', size: 512 },
];

async function generateFavicon(svgBuffer, name, size) {
  const outputPath = path.join(publicDir, name);

  try {
    await sharp(svgBuffer, { density: 300 })
      .resize(size, size, {
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .png()
      .toFile(outputPath);

    console.log(`✓ Generated ${name} (${size}x${size})`);
    return true;
  } catch (error) {
    console.error(`✗ Failed to generate ${name}:`, error.message);
    return false;
  }
}

async function generateFavicons() {
  console.log('🎨 Generating favicon files from SVG...');
  console.log(`Source: ${svgFile}\n`);

  if (!fs.existsSync(svgFile)) {
    console.error(`✗ SVG file not found: ${svgFile}`);
    process.exit(1);
  }

  const svgBuffer = fs.readFileSync(svgFile);

  let successCount = 0;
  let failCount = 0;

  // Generate each favicon sequentially
  for (const { name, size } of sizes) {
    const success = await generateFavicon(svgBuffer, name, size);
    if (success) {
      successCount++;
    } else {
      failCount++;
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log(`✅ Favicon generation complete!`);
  console.log(`   Success: ${successCount}/${sizes.length}`);
  if (failCount > 0) {
    console.log(`   Failed: ${failCount}`);
  }
  console.log(`   Files saved to: ${publicDir}`);
  console.log('='.repeat(50));
}

generateFavicons().catch(error => {
  console.error('Error generating favicons:', error);
  process.exit(1);
});
