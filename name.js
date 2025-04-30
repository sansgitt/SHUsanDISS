import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the game_images directory
const GAME_IMAGES_DIR = path.join(__dirname, 'static', 'game_images');

async function removeNumbersFromFilenames() {
  try {
    console.log(`Cleaning up filenames in ${GAME_IMAGES_DIR}`);

    // Check if directory exists
    try {
      await fs.access(GAME_IMAGES_DIR);
    } catch (error) {
      console.error(`Error: Directory ${GAME_IMAGES_DIR} does not exist`);
      return;
    }

    // Get all files in the directory
    const files = await fs.readdir(GAME_IMAGES_DIR);
    const imageFiles = files.filter(file => 
      file.match(/\.(jpg|jpeg|png|gif)$/i)
    );

    console.log(`Found ${imageFiles.length} image files`);
    
    // Print some example filenames to see the pattern
    console.log("\nExample filenames:");
    for (let i = 0; i < Math.min(5, imageFiles.length); i++) {
      console.log(`  ${imageFiles[i]}`);
    }
    
    // Process each file
    let renamedCount = 0;
    
    for (const file of imageFiles) {
      // More flexible pattern matching for various number formats
      // This will match patterns like:
      // - "cat_bengal (4).jpg"
      // - "cat_bengal(4).jpg"
      // - "cat_bengal 4.jpg"
      // - "cat_bengal_4.jpg"
      
      // Extract the extension
      const extIndex = file.lastIndexOf('.');
      if (extIndex === -1) continue; // Skip files without extension
      
      const extension = file.substring(extIndex);
      const nameWithoutExt = file.substring(0, extIndex);
      
      // Check for various number patterns
      const patterns = [
        /\s*$$\d+$$$/,      // Matches " (4)" or "(4)"
        /\s*\[\d+\]$/,      // Matches " [4]" or "[4]"
        /\s+\d+$/,          // Matches " 4"
        /_\d+$/             // Matches "_4"
      ];
      
      let matched = false;
      let newName = nameWithoutExt;
      
      for (const pattern of patterns) {
        if (pattern.test(nameWithoutExt)) {
          newName = nameWithoutExt.replace(pattern, '');
          matched = true;
          break;
        }
      }
      
      if (!matched) continue; // No pattern matched, skip this file
      
      newName = newName + extension;
      
      // Check if the new name already exists
      if (imageFiles.includes(newName) && newName !== file) {
        console.log(`Skipping ${file} - ${newName} already exists`);
        continue;
      }
      
      // Rename the file
      const oldPath = path.join(GAME_IMAGES_DIR, file);
      const newPath = path.join(GAME_IMAGES_DIR, newName);
      
      await fs.rename(oldPath, newPath);
      console.log(`Renamed: ${file} -> ${newName}`);
      renamedCount++;
    }
    
    console.log(`\nDone! Renamed ${renamedCount} files.`);
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

// Run the function
removeNumbersFromFilenames();