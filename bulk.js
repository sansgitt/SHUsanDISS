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
const cat_breeds = ['Abyssinian', 'Bengal', 'Birman', 'Bombay', 'British Shorthair', 'Egyptian Mau', 'Maine Coon',
                   'Persian', 'Ragdoll', 'Russian Blue', 'Siamese', 'Sphynx'];
const dog_breeds = ['American Bulldog', 'Basset Hound', 'Beagle', 'Boxer', 'Chihuahua', 'English Cocker Spaniel',
                   'English Setter', 'German Shorthaired', 'Great Pyrenees', 'Newfoundland', 'Pomeranian', 'Shiba Inu'];

// Helper function to ask questions
function askQuestion(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
    });
  });
}

async function ensureDirectoryExists(directory) {
  try {
    await fs.mkdir(directory, { recursive: true });
    console.log(`Directory created: ${directory}`);
  } catch (error) {
    if (error.code !== 'EEXIST') {
      console.error(`Error creating directory: ${error.message}`);
    }
  }
}

async function main() {
  try {
    // Ask for source directory
    const sourceDir = await askQuestion("Enter the path to the directory containing your breed images: ");
    if (!sourceDir) {
      console.log("No directory specified. Exiting.");
      rl.close();
      return;
    }
    
    // Ask for target directory
    const targetDir = await askQuestion("Enter the path to save renamed images [static/game_images]: ") || "static/game_images";
    
    // Ensure target directory exists
    await ensureDirectoryExists(targetDir);
    
    // Get all image files
    const files = await fs.readdir(sourceDir);
    const imageFiles = files.filter(file => 
      file.match(/\.(jpg|jpeg|png|gif)$/i)
    );
    
    if (imageFiles.length === 0) {
      console.log(`No image files found in ${sourceDir}`);
      rl.close();
      return;
    }
    
    console.log(`Found ${imageFiles.length} images`);
    
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
    const formattedBreed = selectedBreed.toLowerCase().replace(/\s+/g, '_');
    const speciesLower = selectedSpecies.toLowerCase();
    
    // Rename and copy all images
    for (let i = 0; i < imageFiles.length; i++) {
      const sourceFile = path.join(sourceDir, imageFiles[i]);
      const targetFile = path.join(
        targetDir, 
        `${speciesLower}_${formattedBreed}_${i + 1}.jpg`
      );
      
      await fs.copyFile(sourceFile, targetFile);
      console.log(`Copied: ${imageFiles[i]} -> ${path.basename(targetFile)}`);
    }
    
    console.log("\nAll done! Your breed images are renamed and ready to use.");
    console.log(`The images have been copied to ${targetDir} with consistent naming.`);
    console.log("Restart your Flask app to use these images in the game.");
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  } finally {
    rl.close();
  }
}

// Run the main function
main();
