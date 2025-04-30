import fs from "fs/promises"
import path from "path"
import { fileURLToPath } from "url"
import { dirname } from "path"
import readline from "readline"

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
})

// Define the species and breeds from your Flask app
const species = ["Cat", "Dog"]
const cat_breeds = [
  "Abyssinian",
  "Bengal",
  "Birman",
  "Bombay",
  "British Shorthair",
  "Egyptian Mau",
  "Maine Coon",
  "Persian",
  "Ragdoll",
  "Russian Blue",
  "Siamese",
  "Sphynx",
]
const dog_breeds = [
  "American Bulldog",
  "Basset Hound",
  "Beagle",
  "Boxer",
  "Chihuahua",
  "English Cocker Spaniel",
  "English Setter",
  "German Shorthaired",
  "Great Pyrenees",
  "Newfoundland",
  "Pomeranian",
  "Shiba Inu",
]

// Path to the game_images directory
const GAME_IMAGES_DIR = path.join(__dirname, "static", "game_images")

// Helper function to ask questions
function askQuestion(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer)
    })
  })
}

async function renameImages() {
  try {
    console.log(`Renaming images in ${GAME_IMAGES_DIR}`)

    // Check if directory exists
    try {
      await fs.access(GAME_IMAGES_DIR)
    } catch (error) {
      console.error(`Error: Directory ${GAME_IMAGES_DIR} does not exist`)
      return
    }

    // Get all files in the directory
    const files = await fs.readdir(GAME_IMAGES_DIR)
    const imageFiles = files.filter((file) => file.match(/\.(jpg|jpeg|png|gif)$/i))

    console.log(`Found ${imageFiles.length} image files`)

    // Ask if user wants to rename all images
    const renameAll = await askQuestion("Do you want to rename all images to match the expected format? (y/n): ")

    if (renameAll.toLowerCase() !== "y") {
      console.log("Exiting without renaming.")
      rl.close()
      return
    }

    // For each image, ask for species and breed
    for (const imageFile of imageFiles) {
      console.log(`\nProcessing: ${imageFile}`)

      // Ask for species
      console.log("Species options:")
      species.forEach((s, i) => console.log(`${i + 1}. ${s}`))
      const speciesChoice = await askQuestion("Enter the number for the species (or press Enter to skip this file): ")

      if (!speciesChoice) {
        console.log("Skipping this file.")
        continue
      }

      const selectedSpecies = species[Number.parseInt(speciesChoice) - 1]

      if (!selectedSpecies) {
        console.log("Invalid species selection. Skipping this file.")
        continue
      }

      // Ask for breed
      console.log(`\n${selectedSpecies} breed options:`)
      const breedList = selectedSpecies === "Cat" ? cat_breeds : dog_breeds
      breedList.forEach((b, i) => console.log(`${i + 1}. ${b}`))
      const breedChoice = await askQuestion("Enter the number for the breed (or press Enter to skip this file): ")

      if (!breedChoice) {
        console.log("Skipping this file.")
        continue
      }

      const selectedBreed = breedList[Number.parseInt(breedChoice) - 1]

      if (!selectedBreed) {
        console.log("Invalid breed selection. Skipping this file.")
        continue
      }

      // Format the new filename
      const speciesLower = selectedSpecies.toLowerCase()
      const breedLower = selectedBreed.toLowerCase().replace(/\s+/g, "_")
      const newFilename = `${speciesLower}_${breedLower}.jpg`

      // Check if target file already exists
      if (imageFiles.includes(newFilename) && imageFile !== newFilename) {
        const overwrite = await askQuestion(`File ${newFilename} already exists. Overwrite? (y/n): `)
        if (overwrite.toLowerCase() !== "y") {
          console.log("Skipping this file.")
          continue
        }
      }

      // Rename the file
      try {
        await fs.rename(path.join(GAME_IMAGES_DIR, imageFile), path.join(GAME_IMAGES_DIR, newFilename))
        console.log(`Renamed: ${imageFile} -> ${newFilename}`)
      } catch (error) {
        console.error(`Error renaming ${imageFile}: ${error.message}`)
      }
    }

    console.log("\nAll done! Your breed images have been renamed.")
  } catch (error) {
    console.error(`Error renaming images: ${error.message}`)
  } finally {
    rl.close()
  }
}

// Run the rename function
renameImages()
