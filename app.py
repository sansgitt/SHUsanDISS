from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
import os
import tensorflow as tf
import numpy as np
from werkzeug.utils import secure_filename
import datetime
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
import json
from bson import json_util
import random
import uuid
import re 

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['MONGO_URI'] = "mongodb://localhost:27017/breedclassify"
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Initialize MongoDB
mongo = PyMongo(app)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs('static/game_images', exist_ok=True)

species = ['Cat', 'Dog']
cat_breeds = ['Bengal', 'Russian Blue', 'Persian', 'Birman', 'Abyssinian', 'British Shorthair', 'Maine Coon',
              'Egyptian Mau', 'Bombay', 'Ragdoll', 'Siamese', 'Sphynx']
dog_breeds = ['Basset Hound', 'American Bulldog', 'English Cocker Spaniel', 'Chihuahua', 'Beagle', 'English Setter',
              'German Shorthaired', 'Boxer', 'Pomeranian', 'Great Pyrenees', 'Newfoundland', 'Shiba Inu']

breed_mapping = {
    'Cat': cat_breeds,
    'Dog': dog_breeds
}

idx_to_species = {i: s for i, s in enumerate(species)}
species_to_idx = {s: i for i, s in enumerate(species)}

all_breeds = []
for s in species:
    for b in (cat_breeds if s == 'Cat' else dog_breeds):
        all_breeds.append(f"{s}_{b}")

idx_to_breed = {i: b for i, b in enumerate(all_breeds)}
breed_to_idx = {b: i for i, b in enumerate(all_breeds)}

# Breed facts for the game
breed_facts = {
    # Cat breeds
    'Abyssinian': 'Known for their playful and curious nature, Abyssinians are one of the oldest known cat breeds.',
    'Bengal': 'Bengals are active, playful cats with a distinctive wild appearance. Their coat features spotted or marbled patterns reminiscent of their Asian leopard cat ancestry.',
    'Birman': 'Birmans are known for their striking blue eyes and white-gloved paws, with a silky medium-length coat.',
    'Bombay': 'Bombyas were developed to resemble miniature black panthers, with sleek black coats and copper eyes.',
    'British Shorthair': 'British Shorthairs are known for their dense, plush coats and round faces with chubby cheeks.',
    'Egyptian Mau': 'Egyptian Maus are the only naturally spotted domestic cat breed and are also one of the fastest.',
    'Maine Coon': 'Maine Coons are one of the largest domestic cat breeds, known for their tufted ears and bushy tails.',
    'Persian': 'Persians are known for their long, luxurious coats and flat faces with round, expressive eyes.',
    'Ragdoll': 'Ragdolls are known for going limp when picked up, hence their name. They have striking blue eyes.',
    'Russian Blue': 'Russian Blues have a distinctive bluish-gray coat and emerald green eyes, with a shy but playful personality.',
    'Siamese': 'Siamese cats are known for their striking blue almond-shaped eyes and color-point coats.',
    'Sphynx': 'Sphynx cats are known for being hairless, though they often have a fine down covering their bodies.',

    # Dog breeds
    'American Bulldog': 'American Bulldogs are strong, athletic working dogs known for their loyalty and protective nature.',
    'Basset Hound': 'Basset Hounds have a keen sense of smell second only to the Bloodhound, with distinctive long ears.',
    'Beagle': 'Beagles are friendly, curious scent hounds with an excellent sense of smell. They are known for their melodious howl and happy-go-lucky personality.',
    'Boxer': 'Boxers are energetic, playful dogs known for their distinctive squared muzzle and underbite.',
    'Chihuahua': 'Chihuahuas are the smallest dog breed in the world, known for their big personalities despite their tiny size.',
    'English Cocker Spaniel': 'English Cocker Spaniels are known for their silky coats and gentle, merry temperament.',
    'English Setter': 'English Setters are known for their speckled coat pattern called "belton" and their elegant appearance.',
    'German Shorthaired': 'German Shorthaired Pointers are versatile hunting dogs known for their intelligence and athleticism.',
    'Great Pyrenees': 'Great Pyrenees are large, powerful guardian dogs with thick white coats, historically used to protect sheep.',
    'Newfoundland': 'Newfoundlands are massive water rescue dogs with webbed feet and water-resistant coats.',
    'Pomeranian': 'Pomeranians are small, fluffy spitz-type dogs known for their fox-like faces and vibrant personalities.',
    'Shiba Inu': 'Shiba Inus are ancient Japanese hunting dogs known for their fox-like appearance and independent nature.'
}

# Basic profanity list (you need to expand this significantly)
PROFANE_WORDS = ["anal", "anus", "arse", "ass", "ballsack", "balls", "bastard", "bitch", "bloody", "blowjob", "bollock", "bollok", "boner", "boob", "butt", "butthole", "cunt", "damn", "dick", "dildo", "dyke", "fag", "feck", "fellate", "fellatio", "felching", "fuck", "fudgepacker", "flange", "goddamn", "godsdamn", "handjob", "hardcore", "jerk", "jugs", "kike", "knob", "labia", "lmao", "lmfao", "muff", "nigger", "nigga", "omg", "penis", "piss", "poop", "prick", "pubic", "pussy", "queer", "scrotum", "sex", "shit", "slut", "smegma", "spunk", "suck", "tits", "tosser", "turd", "twat", "vagina", "wank", "whore"] 

def contains_profanity(text):
    """Checks if text contains any words from the profane list."""
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    # Use regex to find whole word matches, handling punctuation and case
    # This regex looks for word boundaries (\b) around the profane words.
    for word in PROFANE_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            return True
    return False


# Add this function to debug and list available breed images
def list_game_images():
    """List all images in the game_images directory"""
    game_images_dir = 'static/game_images'
    if not os.path.exists(game_images_dir):
        logger.warning(f"Directory not found: {game_images_dir}")
        return []

    files = os.listdir(game_images_dir)
    image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]

    logger.debug(f"Found {len(image_files)} images in {game_images_dir}: {image_files}")
    return image_files

# Call this function at startup to see what images are available
available_images = list_game_images()


# Load model
try:
    model = tf.keras.models.load_model('petspecies_catdogclassify.h5')
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # Create a fallback function if model isn't available (for testing purposes)
    def mock_predict(img_array):
        return [np.array([[0.8, 0.2]]), np.array([[0.05, 0.1, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
                                                  0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]])]
    model = type('MockModel', (), {'predict': mock_predict})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# User Authentication Routes
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Check if user already exists
    existing_user = mongo.db.users.find_one({'email': data['email']})
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already registered'})

    # Hash the password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    # Create new user
    new_user = {
        'name': data['name'],
        'email': data['email'],
        'password': hashed_password,
        'created_at': datetime.datetime.now(),
        'high_score': 0  # Initialize high score
    }

    # Insert user into database
    mongo.db.users.insert_one(new_user)

    # Log activity
    log_activity('registration', new_user['_id'], new_user['name'])

    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    # Find user in database
    user = mongo.db.users.find_one({'email': data['email']})

    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        # Create session
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        return jsonify({
            'success': True,
            'user': {
                'name': user['name'],
                'email': user['email']
            }
        })

    return jsonify({'success': False, 'message': 'Invalid email or password'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'name': session.get('user_name'),
                'email': session.get('user_email')
            }
        })
    return jsonify({'authenticated': False})

# Community Pawprints Routes
@app.route('/api/pawprints', methods=['GET'])
def get_pawprints():
    try:
        # Get all pawprints, sorted by newest first
        pawprints = list(mongo.db.pawprints.find().sort('created_at', -1))

        # Convert ObjectId to string for JSON serialization and format datetimes
        for pawprint in pawprints:
            pawprint['_id'] = str(pawprint['_id'])
            if isinstance(pawprint['created_at'], datetime.datetime):
                 pawprint['created_at'] = pawprint['created_at'].isoformat()


        return jsonify({
            'success': True,
            'pawprints': pawprints
        })
    except Exception as e:
        print(f"Error in get_pawprints: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving pawprints: {str(e)}'
        })

@app.route('/api/pawprints', methods=['POST'])
def add_pawprint():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})

    file = request.files['file']
    pet_type = request.form.get('pet_type')
    caption = request.form.get('caption', '') # Get caption, default to empty string

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    if file and allowed_file(file.filename):
        # --- Profanity Filtering for Caption ---
        if contains_profanity(caption):
            log_activity('profanity_detected_caption', session['user_id'], session['user_name'], caption=caption)
            return jsonify({'success': False, 'message': 'Your caption contains inappropriate language.'})
        # --- End Profanity Filtering ---

        # Generate a unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Create new pawprint
        new_pawprint = {
            'user_id': session['user_id'],
            'user_name': session['user_name'],
            'pet_type': pet_type,
            'caption': caption.strip(), # Store stripped caption
            'image_path': f"/uploads/{filename}",
            'created_at': datetime.datetime.now()
        }

        # Insert into database
        result = mongo.db.pawprints.insert_one(new_pawprint)

        # Log activity
        log_activity('pawprint', session['user_id'], session['user_name'], pet_type=pet_type, caption=caption)

        return jsonify({'success': True, 'message': 'Pawprint added successfully'})

    return jsonify({'success': False, 'message': 'File type not allowed'})


# User Profile Routes
@app.route('/api/user/uploads', methods=['GET'])
def get_user_uploads():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})

    try:
        # Get user's recent uploads (both AI model and community posts)
        ai_uploads = list(mongo.db.predictions.find({'user_id': session['user_id']}).sort('created_at', -1).limit(3))
        community_uploads = list(mongo.db.pawprints.find({'user_id': session['user_id']}).sort('created_at', -1).limit(3))

        # Get user's high score
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        high_score = user.get('high_score', 0) if user else 0

        # Convert ObjectId to string for JSON serialization and format datetimes
        for upload in ai_uploads:
            upload['_id'] = str(upload['_id'])
            if isinstance(upload['created_at'], datetime.datetime):
                 upload['created_at'] = upload['created_at'].isoformat()

        for upload in community_uploads:
            upload['_id'] = str(upload['_id'])
            if isinstance(upload['created_at'], datetime.datetime):
                 upload['created_at'] = upload['created_at'].isoformat()


        return jsonify({
            'success': True,
            'ai_uploads': ai_uploads,
            'community_uploads': community_uploads,
            'high_score': high_score
        })
    except Exception as e:
        print(f"Error in get_user_uploads: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving uploads: {str(e)}'
        })

# Admin Dashboard Routes
@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})

    # Get statistics
    total_users = mongo.db.users.count_documents({})
    total_predictions = mongo.db.predictions.count_documents({})
    total_pawprints = mongo.db.pawprints.count_documents({})
    cat_count = mongo.db.pawprints.count_documents({'pet_type': 'cat'})
    dog_count = mongo.db.pawprints.count_documents({'pet_type': 'dog'})

    # Get all users
    users = list(mongo.db.users.find())
    for user in users:
        user['_id'] = str(user['_id'])
        # Don't send password hash to client
        if 'password' in user:
            del user['password']

    # Get recent activity (combine predictions, pawprints, and registrations)
    recent_predictions = list(mongo.db.predictions.find().sort('created_at', -1).limit(10))
    for pred in recent_predictions:
        pred['_id'] = str(pred['_id'])
        pred['type'] = 'prediction'
        pred['timestamp'] = pred['created_at']
        if isinstance(pred['timestamp'], datetime.datetime):
            pred['timestamp'] = pred['timestamp'].isoformat()


    recent_pawprints = list(mongo.db.pawprints.find().sort('created_at', -1).limit(10))
    for pawprint in recent_pawprints:
        pawprint['_id'] = str(pawprint['_id'])
        pawprint['type'] = 'pawprint'
        pawprint['timestamp'] = pawprint['created_at']
        if isinstance(pawprint['timestamp'], datetime.datetime):
            pawprint['timestamp'] = pawprint['timestamp'].isoformat()


    # Combine and sort by timestamp
    all_activity = recent_predictions + recent_pawprints
    all_activity.sort(key=lambda x: x['timestamp'], reverse=True)

    # Limit to 20 most recent activities
    recent_activity = all_activity[:20]

    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'total_predictions': total_predictions,
            'total_pawprints': total_pawprints,
            'cat_count': cat_count,
            'dog_count': dog_count
        },
        'users': users,
        'recent_activity': recent_activity
    })


# Helper function to log activity
def log_activity(activity_type, user_id, user_name, **kwargs):
    activity = {
        'type': activity_type,
        'user_id': user_id,
        'user_name': user_name,
        'timestamp': datetime.datetime.now()
    }

    # Add any additional data
    for key, value in kwargs.items():
        activity[key] = value

    mongo.db.activity_log.insert_one(activity)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pawprints')
def pawprints():
    return render_template('pawprint.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/static/game_images/<filename>')
def game_image(filename):
    return send_from_directory('static/game_images', filename)

# Add this to the beginning of the predict function
@app.route('/predict', methods=['POST'])
def predict():
    logger.debug("Predict endpoint called")
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwriting
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            img = tf.keras.preprocessing.image.load_img(filepath, target_size=(224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0) / 255.0

            predictions = model.predict(img_array)

            # Get species prediction
            species_idx = np.argmax(predictions[0][0])
            species_name = idx_to_species[species_idx]
            species_confidence = float(predictions[0][0][species_idx] * 100)

            # Filter breed predictions by species
            breed_predictions = predictions[1][0]
            filtered_breeds = []

            # Get breed indices for the predicted species
            for i, breed_full_name in idx_to_breed.items():
                if breed_full_name.startswith(f"{species_name}_"):
                    breed_name = breed_full_name.split('_')[1]
                    confidence = float(breed_predictions[i] * 100)
                    filtered_breeds.append({
                        "index": i,
                        "breed": breed_name,
                        "confidence": confidence
                    })

            filtered_breeds.sort(key=lambda x: x['confidence'], reverse=True)

            # Set a confidence threshold for breed identification
            confidence_threshold = 50.0

            if filtered_breeds and filtered_breeds[0]['confidence'] >= confidence_threshold:
                top_breed = filtered_breeds[0]['breed']
                top_breed_confidence = filtered_breeds[0]['confidence']
            else:
                top_breed = "Unknown"
                top_breed_confidence = filtered_breeds[0]['confidence'] if filtered_breeds else 0.0

            top_breeds = filtered_breeds[:3] if filtered_breeds else []
            top_breeds_simplified = [{"breed": b["breed"], "confidence": b["confidence"]} for b in top_breeds]

            # Save processed image path (in a real app, you would apply image processing here)
            processed_path = f"/uploads/{filename}"  # Just using the original image for simplicity

            # Save prediction to database if user is logged in
            if 'user_id' in session:
                prediction_data = {
                    'user_id': session['user_id'],
                    'user_name': session['user_name'],
                    'species': species_name,
                    'breed': top_breed,
                    'confidence': top_breed_confidence,
                    'image_path': processed_path,
                    'created_at': datetime.datetime.now()
                }
                mongo.db.predictions.insert_one(prediction_data)

                # Log activity
                log_activity('prediction', session['user_id'], session['user_name'],
                            species=species_name, breed=top_breed)

            result = {
                "species": species_name,
                "species_confidence": round(species_confidence, 2),
                "breed": top_breed,
                "breed_confidence": round(top_breed_confidence, 2),
                "top_breeds": top_breeds_simplified,
                "image_path": processed_path
            }

            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f"Error processing image: {str(e)}"})

    return jsonify({'error': 'File type not allowed'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Service is running'})

# Add this new route after the health_check route
@app.route('/test-db')
def test_db():
    try:
        # List all collections in the database
        collections = mongo.db.list_collection_names()
        # Count documents in each collection
        counts = {}
        for collection in collections:
            counts[collection] = mongo.db.get_collection(collection).count_documents({})

        return jsonify({
            'status': 'success',
            'message': 'Connected to MongoDB successfully!',
            'collections': collections,
            'document_counts': counts
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to MongoDB: {str(e)}'
        })

# Add this new route after the test-db route
@app.route('/debug-session')
def debug_session():
    return jsonify({
        'session': {
            'user_id': session.get('user_id'),
            'user_name': session.get('user_name'),
            'user_email': session.get('user_email')
        },
        'is_authenticated': 'user_id' in session
    })

# Game Routes
@app.route('/api/game/new', methods=['POST'])
def new_game():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})

    try:
        # Create a new game with 10 rounds
        game_id = str(uuid.uuid4())
        rounds = []

        # Track used images filenames to avoid duplicates within a game
        used_images_filenames = set()

        # Create 10 rounds with random breeds
        for i in range(10):
            # Randomly choose cat or dog
            species = random.choice(['Cat', 'Dog'])

            # Get breeds for the chosen species
            breeds = cat_breeds if species == 'Cat' else dog_breeds

            # Choose the correct breed
            correct_breed = random.choice(breeds)

            # Get 3 wrong options
            wrong_options = random.sample([b for b in breeds if b != correct_breed], 3)

            # Create options (1 correct, 3 wrong)
            options = [correct_breed] + wrong_options
            random.shuffle(options)

            # Get a fact about the breed
            fact = breed_facts.get(correct_breed, f"This is a {correct_breed}.")

            # Find all available images for the correct breed based on filename patterns
            species_lower = species.lower()
            breed_lower = correct_breed.lower().replace(' ', '_')

            # Look for files starting with species_breed or just breed
            possible_image_files = [f for f in available_images if f.startswith(f"{species_lower}_{breed_lower}") or f.startswith(f"{breed_lower}")]

            chosen_image_file = None
            image_path = "/static/placeholder.jpg" # Default to placeholder

            if possible_image_files:
                # Filter out already used images by filename
                available_to_use = [f for f in possible_image_files if f not in used_images_filenames]

                if not available_to_use:
                    # If all specific images for this breed are used, allow reusing one from the possible list
                     logger.warning(f"All unique images for {correct_breed} used, allowing reuse.")
                     available_to_use = possible_image_files # Use possible_image_files to pick from any available for the breed

                if available_to_use:
                    chosen_image_file = random.choice(available_to_use)
                    image_path = f"/static/game_images/{chosen_image_file}"
                    # Add the chosen image filename to used set
                    used_images_filenames.add(chosen_image_file)
                else:
                     logger.warning(f"No available images for {correct_breed} after filtering used images.")


            if chosen_image_file is None:
                 logger.warning(f"No image found for {species} {correct_breed}, using placeholder.")
                 # If placeholder is used, add its path to avoid re-logging in this game instance
                 used_images_filenames.add(image_path)


            rounds.append({
                'species': species,
                'correct_breed': correct_breed,
                'options': options,
                'image_path': image_path,
                'fact': fact
            })

        # Store game in session
        session['current_game'] = {
            'id': game_id,
            'rounds': rounds,
            'current_round': 0,
            'score': 0,
            'start_time': datetime.datetime.now().isoformat(),
            'used_images_filenames': list(used_images_filenames) # Store used filenames in session
        }

        return jsonify({
            'success': True,
            'game_id': game_id,
            'total_rounds': len(rounds),
            'first_round': rounds[0]
        })
    except Exception as e:
        logger.error(f"Error creating new game: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error creating new game: {str(e)}'
        })

@app.route('/api/game/submit', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'})

    if 'current_game' not in session:
        return jsonify({'success': False, 'message': 'No active game'})

    try:
        data = request.get_json()
        selected_breed = data.get('breed')

        game = session['current_game']
        current_round = game['current_round']

        if current_round >= len(game['rounds']):
            return jsonify({'success': False, 'message': 'Game already complete'})

        round_data = game['rounds'][current_round]
        correct = selected_breed == round_data['correct_breed']

        # Update score if correct
        if correct:
            game['score'] += 1

        # Move to next round
        game['current_round'] += 1
        game_complete = game['current_round'] >= len(game['rounds'])

        # Update session
        session['current_game'] = game

        response = {
            'success': True,
            'correct': correct,
            'correct_breed': round_data['correct_breed'],
            'fact': round_data['fact'],
            'score': game['score'],
            'game_complete': game_complete
        }

        # If game is complete, update high score if needed
        if game_complete:
            user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
            current_high_score = user.get('high_score', 0)

            if game['score'] > current_high_score:
                mongo.db.users.update_one(
                    {'_id': ObjectId(session['user_id'])},
                    {'$set': {'high_score': game['score']}}
                )
                response['new_high_score'] = True
                response['old_high_score'] = current_high_score

            # Save game result to database
            game_result = {
                'user_id': session['user_id'],
                'user_name': session['user_name'],
                'score': game['score'],
                'total_rounds': len(game['rounds']),
                'created_at': datetime.datetime.now()
            }
            mongo.db.game_results.insert_one(game_result)

            # Log activity
            log_activity('game_completed', session['user_id'], session['user_name'],
                        score=game['score'], total_rounds=len(game['rounds']))
        else:
            # If game is not complete, include next round
            response['next_round'] = game['rounds'][game['current_round']]

        return jsonify(response)
    except Exception as e:
        print(f"Error submitting answer: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error submitting answer: {str(e)}'
        })

@app.route('/api/game/high-scores', methods=['GET'])
def get_high_scores():
    try:
        # Get top 10 high scores
        high_scores = list(mongo.db.users.find(
            {'high_score': {'$gt': 0}},
            {'name': 1, 'high_score': 1, '_id': 0}
        ).sort('high_score', -1).limit(10))

        # Get user's high score if logged in
        user_high_score = None
        if 'user_id' in session:
            user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
            if user:
                user_high_score = {
                    'name': user['name'],
                    'high_score': user.get('high_score', 0)
                }

        return jsonify({
            'success': True,
            'high_scores': high_scores,
            'user_high_score': user_high_score
        })
    except Exception as e:
        print(f"Error getting high scores: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting high scores: {str(e)}'
        })

@app.route('/static/placeholder.jpg')
def placeholder_image():
    # Return a simple placeholder image
    return send_from_directory('static', 'placeholder.jpg')

if __name__ == '__main__':
    app.run(debug=True)