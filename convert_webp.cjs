const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Install sharp locally
console.log('Installing sharp...');
execSync('npm install sharp --no-save', { cwd: __dirname, stdio: 'inherit' });

const sharp = require('sharp');

const imagesDir = path.join(__dirname, 'Bali', 'bali-code', 'bali-code', 'bali-frontend', 'src', 'assets', 'images');
const publicDir = path.join(__dirname, 'Bali', 'bali-code', 'bali-code', 'bali-frontend', 'public', 'images');

async function convertToWebp(dir, filename) {
    const src = path.join(dir, filename);
    const dest = path.join(dir, filename.replace(/\.png$/i, '.webp'));
    if (!fs.existsSync(src)) { console.log(`  SKIP: ${filename} not found`); return; }
    const info = await sharp(src).webp({ quality: 80 }).toFile(dest);
    const origSize = fs.statSync(src).size;
    console.log(`  ✅ ${filename}: ${(origSize / 1024).toFixed(0)}KB → ${(info.size / 1024).toFixed(0)}KB (${((1 - info.size / origSize) * 100).toFixed(0)}% smaller)`);
}

async function main() {
    console.log('\n📁 Converting src/assets/images...');
    await convertToWebp(imagesDir, 'banner2.png');
    await convertToWebp(imagesDir, 'mobile-banner2.png');
    await convertToWebp(imagesDir, 'hero-banner.png');
    await convertToWebp(imagesDir, 'hero-l-star.png');
    await convertToWebp(imagesDir, 'hero-l-star2.png');
    await convertToWebp(imagesDir, 'hero-r-star.png');
    await convertToWebp(imagesDir, 'card.png');
    await convertToWebp(imagesDir, 'right-bottom.png');

    console.log('\n📁 Converting public/images...');
    await convertToWebp(publicDir, 'banner2.png');
    await convertToWebp(publicDir, 'mobile-banner2.png');

    console.log('\n✅ Done!');
}

main().catch(console.error);
