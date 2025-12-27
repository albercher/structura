# Firebase Setup Guide for Structura

This guide will walk you through setting up Firebase Firestore to store and serve protected blueprints for premium domains.

## Prerequisites

- A Google account
- Firebase CLI (optional, for advanced usage)

## Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or **"Create a project"**
3. Enter a project name (e.g., "structura-blueprints")
4. Click **"Continue"**
5. (Optional) Enable Google Analytics - you can skip this
6. Click **"Create project"**
7. Wait for the project to be created, then click **"Continue"**

## Step 2: Enable Firestore Database

1. In your Firebase project, click on **"Firestore Database"** in the left sidebar
2. Click **"Create database"**
3. Choose **"Start in production mode"** (we'll set up security rules later)
4. Select a location for your database (choose the closest to your users)
5. Click **"Enable"**

## Step 3: Create Service Account (for Server-Side Access)

1. In Firebase Console, click the **gear icon** ⚙️ next to "Project Overview"
2. Select **"Project settings"**
3. Go to the **"Service accounts"** tab
4. Click **"Generate new private key"**
5. A JSON file will download - **save this file securely** (this is your service account credentials)
6. **Important**: Never commit this file to git! It's already in `.gitignore`

## Step 4: Set Up Firestore Collections

You need to create two collections in Firestore:

### Collection 1: `blueprints` (for protected blueprints)

1. In Firestore Database, click **"Start collection"**
2. Collection ID: `blueprints`
3. Click **"Next"**
4. Add a document:
   - **Document ID**: `medical` (or any premium domain name)
   - **Fields**:
     - `schema` (type: **string**): Paste the entire JSON schema as a JSON string
   - Click **"Save"**

**Example Document Structure:**

For `medical` domain:
```
Collection: blueprints
Document ID: medical
Fields:
  - schema (string): "{\"title\":\"Medical Lab Report Schema\",\"type\":\"object\",\"properties\":{\"patient_name\":{\"type\":\"string\"},\"test_date\":{\"type\":\"string\",\"format\":\"date\"}},\"required\":[\"patient_name\",\"test_date\"]}"
```

**Important:** The schema must be stored as a JSON string, not as a map/object. You can:
- Copy your JSON schema and paste it directly as a string
- Use a JSON minifier to convert formatted JSON to a single-line string
- The system will automatically parse the JSON string when retrieving the blueprint

### Collection 2: `api_keys` (for API key validation)

**Why you need this:** This collection stores API keys that grant access to protected blueprints. When users request premium domains (like `medical`, `legal`, etc.), they must provide a valid API key. The system checks this collection to:
- Verify the API key exists and is active
- Check which domains the key has access to
- Enable monetization and access control for premium blueprints

1. Click **"Start collection"** again
2. Collection ID: `api_keys`
3. Click **"Next"**
4. Add a document:
   - **Document ID**: Your API key (e.g., `test-api-key-123`)
   - **Fields**:
     - `active` (type: **boolean**): `true` - Set to `false` to revoke access
     - `allowed_domains` (type: **array**): `["medical", "legal", "finance"]` or `["*"]` for all domains
     - `created_at` (type: **timestamp**): Current date/time
     - `expires_at` (type: **timestamp**, optional): Expiration date for time-limited access
   - Click **"Save"**

**Example Document Structure:**

```
Collection: api_keys
Document ID: test-api-key-123
Fields:
  - active: true
  - allowed_domains: ["medical", "legal"]
  - created_at: 2024-01-01T00:00:00Z
```

**Note:** Without this collection, users won't be able to access protected blueprints. Each API key document controls access to specific premium domains.

## Step 5: Configure Environment Variables

1. Open your downloaded service account JSON file
2. Copy the entire JSON content
3. Update your `.env` file:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id-here
FIREBASE_COLLECTION=blueprints
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...@....iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/...%40....iam.gserviceaccount.com"}
```

**Tips:**
- You can paste the JSON as-is (multi-line) or minify it (single line)
- The private key can have `\n` for newlines or actual newlines
- Python's `json.loads()` handles both formats
- This works for both local development and Railway/cloud deployment

**To find your Project ID:**
- In Firebase Console, click the gear icon ⚙️ → "Project settings"
- The Project ID is shown at the top (e.g., `structura-blueprints-abc123`)

**Important**: 
- Never commit the service account JSON content to version control
- Keep your `.env` file in `.gitignore` (it already is)

## Step 6: Install Firebase Admin SDK

The Firebase Admin SDK is already in `requirements.txt`. Install it:

```bash
pip install firebase-admin
```

## Step 7: Test Your Setup

Create a test script to verify Firebase connection:

```python
# test_firebase.py
import asyncio
from src.blueprints.firebase_client import FirebaseBlueprintClient

async def test_firebase():
    try:
        client = FirebaseBlueprintClient()
        # Test with a valid API key
        blueprint = await client.get_blueprint("medical", api_key="test-api-key-123")
        print("✅ Firebase connection successful!")
        print(f"Blueprint keys: {list(blueprint.keys())}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_firebase())
```

Run it:
```bash
python test_firebase.py
```

## Step 9: Set Up Security Rules (Recommended)

1. In Firestore, go to **"Rules"** tab
2. Update the rules to restrict access:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read access to blueprints only for authenticated service accounts
    match /blueprints/{domain} {
      allow read: if request.auth != null;
      allow write: if false; // Only allow writes via Admin SDK
    }
    
    // API keys collection - only readable by service accounts
    match /api_keys/{apiKey} {
      allow read: if request.auth != null;
      allow write: if false; // Only allow writes via Admin SDK
    }
  }
}
```

3. Click **"Publish"**

**Note**: Since we're using the Admin SDK with service account credentials, these rules mainly protect against direct client access. The Admin SDK bypasses security rules.

## Step 10: Add Your First Premium Blueprint

### Option A: Using Firebase Console (Manual)

1. Go to Firestore Database
2. Click on `blueprints` collection
3. Click **"Add document"**
4. Document ID: `medical` (or your domain name)
5. Add field:
   - Field name: `schema`
   - Type: **string**
   - Value: Paste your entire JSON schema as a JSON string (minified or formatted)
   
**Example:** `{"title":"Medical Lab Report Schema","type":"object","properties":{...}}`

### Option B: Using Python Script (Recommended)

```python
# add_blueprint.py
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Firebase
creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
cred_dict = json.loads(creds_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load your blueprint JSON file
with open("medical_blueprint.json", "r") as f:
    blueprint_schema = json.load(f)

# Convert to JSON string and add to Firestore
# The schema must be stored as a JSON string, not as a dict
doc_ref = db.collection("blueprints").document("medical")
doc_ref.set({
    "schema": json.dumps(blueprint_schema)  # Store as JSON string
})

print("✅ Blueprint added successfully!")
```

## Step 10: Create API Keys

You can create API keys programmatically:

```python
# create_api_key.py
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

# Initialize Firebase
creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
cred_dict = json.loads(creds_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Create an API key
api_key = "premium-user-key-123"
doc_ref = db.collection("api_keys").document(api_key)
doc_ref.set({
    "active": True,
    "allowed_domains": ["medical", "legal", "finance"],  # or ["*"] for all
    "created_at": datetime.now(),
    "expires_at": datetime.now() + timedelta(days=365)  # Optional
})

print(f"✅ API key created: {api_key}")
```

## Troubleshooting

### Error: "Failed to initialize Firebase"
- Verify `FIREBASE_CREDENTIALS_JSON` is set in your environment variables
- Check that the JSON is valid (use a JSON validator like jsonlint.com)
- Ensure `FIREBASE_PROJECT_ID` matches your Firebase project
- Make sure all quotes in the JSON are properly escaped

### Error: "Blueprint not found"
- Verify the document exists in the `blueprints` collection
- Check the document ID matches the domain name exactly
- Ensure the `schema` field exists in the document

### Error: "Access denied - Invalid API key"
- Check the API key exists in the `api_keys` collection
- Verify `active` field is `true`
- Ensure the domain is in `allowed_domains` array (or `*` for all)

### Error: "Permission denied"
- Verify your service account has proper permissions
- Check Firestore security rules (though Admin SDK should bypass them)
- Ensure the service account JSON is from the correct project

## Best Practices

1. **Store credentials securely**: Never commit service account JSON files or `.env` files
2. **Use environment variables**: Keep the JSON file path in `.env`, not hardcoded
3. **Rotate credentials**: Regularly rotate service account keys if compromised
4. **Monitor usage**: Set up Firebase monitoring/alerts
5. **Backup blueprints**: Export blueprints regularly
6. **Version control**: Consider adding version fields to blueprints
7. **File location**: Store the JSON file outside the project root in production, or use absolute paths

## Next Steps

1. Add your premium blueprints to Firestore
2. Create API keys for your users
3. Test the API with premium domains
4. Set up monitoring and alerts in Firebase Console

## Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)

