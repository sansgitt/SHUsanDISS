import fs from "fs/promises"
import path from "path"
import { fileURLToPath } from "url"
import { dirname } from "path"

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

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

async function checkImageNames() {
  try {
    console.log(`Checking images in ${GAME_IMAGES_DIR}`)

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

    // Check for each breed if there's a matching image
    const missingImages = []
    const foundImages = []

    for (const speciesName of species) {
      const breeds = speciesName === "Cat" ? cat_breeds : dog_breeds
      const speciesLower = speciesName.toLowerCase()

      for (const breed of breeds) {
        const breedLower = breed.toLowerCase().replace(/\s+/g, "_")
        const expectedName = `${speciesLower}_${breedLower}.jpg`

        // Check if the exact expected name exists
        if (imageFiles.includes(expectedName)) {
          foundImages.push({ species: speciesName, breed, file: expectedName })
          continue
        }

        // Check for alternative formats
        const alternativeFormats = [
          `${speciesLower}_${breedLower}_1.jpg`,
          `${breedLower}.jpg`,
          `${breed.toLowerCase().replace(/\s+/g, "")}.jpg`,
        ]

        let found = false
        for (const format of alternativeFormats) {
          if (imageFiles.includes(format)) {
            foundImages.push({ species: speciesName, breed, file: format })
            found = true
            break
          }
        }

        // Check for partial matches
        if (!found) {
          const partialMatches = imageFiles.filter(
            (file) => file.includes(breedLower) || file.includes(breed.toLowerCase().replace(/\s+/g, "")),
          )

          if (partialMatches.length > 0) {
            foundImages.push({ species: speciesName, breed, file: partialMatches[0], note: "Partial match" })
            found = true
          }
        }

        if (!found) {
          missingImages.push({ species: speciesName, breed })
        }
      }
    }

    // Print results
    console.log("\nFound images:")
    foundImages.forEach((item) => {
      console.log(`${item.species} ${item.breed}: ${item.file}${item.note ? ` (${item.note})` : ""}`)
    })

    console.log("\nMissing images:")
    missingImages.forEach((item) => {
      console.log(`${item.species} ${item.breed}`)
    })

    console.log("\nSummary:")
    console.log(`Total breeds: ${cat_breeds.length + dog_breeds.length}`)
    console.log(`Found images: ${foundImages.length}`)
    console.log(`Missing images: ${missingImages.length}`)

    // Suggest renaming
    if (foundImages.length > 0 && foundImages.some((item) => item.note)) {
      console.log("\nSuggested renames to match expected format:")
      foundImages
        .filter((item) => item.note)
        .forEach((item) => {
          const expectedName = `${item.species.toLowerCase()}_${item.breed.toLowerCase().replace(/\s+/g, "_")}.jpg`
          console.log(`Rename "${item.file}" to "${expectedName}"`)
        })
    }
  } catch (error) {
    console.error(`Error checking image names: ${error.message}`)
  }
}

// Run the check
checkImageNames()
