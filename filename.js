import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import readline from 'readline';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Define the species and breeds from your Flask app
const species = ['Cat', 'Dog'];
const cat_breeds = [
  'Abyssinian', 'Bengal', 'Birman', 'Bombay', 'British Shorthair', 
  'Egyptian Mau', 'Maine Coon', 'Persian', 'Ragdoll', 
  'Russian Blue', 'Siamese', 'Sphynx'
];
const dog_breeds = [
  'American Bulldog', 'Basset Hound', 'Beagle', 'Boxer', 'Chihuahua', 
  'English Cocker Spaniel', 'English Setter', 'German Shorthaired', 
  'Great Pyrenees', 'Newfoundland', 'Pomeranian', 'Shiba Inu'
];

// Path to the game_images directory
const GAME_IMAGES_DIR = path.join(__dirname, 'static', 'game_images');

// Helper function to ask questions
function askQuestion(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
    });
  });
}

async function preserveAllImages() {
  try {
    console.log(`Renaming images in ${GAME_IMAGES_DIR} while preserving all files`);

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
    
    // Ask for species and breed
    console.log("\nSpecies options:");
    species.forEach((s, i) => console.log(`${i + 1}. ${s}`));
    const speciesChoice = await askQuestion("Enter the number for the species: ");
    const selectedSpecies = species[parseInt(speciesChoice) - 1];
    
    if (!selectedSpecies) {
      console.log("Invalid species selection. Exiting.");
      rl.close();
      return;
    }
    
    console.log(`\n${selectedSpecies} breed options:`);
    const breedList = selectedSpecies === 'Cat' ? cat_breeds : dog_breeds;
    breedList.forEach((b, i) => console.log(`${i + 1}. ${b}`));
    const breedChoice = await askQuestion("Enter the number for the breed: ");
    const selectedBreed = breedList[parseInt(breedChoice) - 1];
    
    if (!selectedBreed) {
      console.log("Invalid breed selection. Exiting.");
      rl.close();
      return;
    }
    
    // Format the breed name
    const speciesLower = selectedSpecies.toLowerCase();
    const breedLower = selectedBreed.toLowerCase().replace(/\s+/g, '_');
    const baseFilename = `${speciesLower}_${breedLower}`;
    
    // Ask for confirmation
    console.log(`\nYou selected: ${selectedSpecies} - ${selectedBreed}`);
    console.log(`All images will be renamed to: ${baseFilename}_1.jpg, ${baseFilename}_2.jpg, etc.`);
    const confirm = await askQuestion("Proceed? (y/n): ");
    
    if (confirm.toLowerCase() !== 'y') {
      console.log("Operation cancelled. Exiting.");
      rl.close();
      return;
    }
    
    // Rename all images
    let renamedCount = 0;
    
    for (let i = 0; i < imageFiles.length; i++) {
      const file = imageFiles[i];
      const newFilename = `${baseFilename}_${i + 1}.jpg`;
      
      try {
        await fs.rename(
          path.join(GAME_IMAGES_DIR, file), 
          path.join(GAME_IMAGES_DIR, newFilename)
        );
        console.log(`Renamed: ${file} -> ${newFilename}`);
        renamedCount++;
      } catch (error) {
        console.error(`Error renaming ${file}: ${error.message}`);
      }
    }
    
    console.log(`\nDone! Renamed ${renamedCount} files to the format: ${baseFilename}_N.jpg`);
    console.log("These images will be recognized by your game.");
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  } finally {
    rl.close();
  }
}

// Run the function
preserveAllImages();