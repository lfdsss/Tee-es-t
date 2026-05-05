#!/usr/bin/env python3
"""Setup Gmail OAuth — run this on your Mac to authorize Gmail access.

Usage:
    python setup_gmail.py

This will:
1. Open your browser for Google OAuth
2. Save the token locally
3. Print the token so you can paste it in Railway
"""

import os
import sys
from pathlib import Path

def main():
    # Install dependencies if needed
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Installation des dependances Google...")
        os.system(f"{sys.executable} -m pip install google-auth google-auth-oauthlib google-api-python-client")
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    config_dir = Path(__file__).parent / "config"
    config_dir.mkdir(exist_ok=True)

    credentials_path = config_dir / "gmail_credentials.json"
    token_path = config_dir / "gmail_token.json"

    # Check if credentials file exists, if not create it from env or prompt
    if not credentials_path.exists():
        env_json = os.getenv("GMAIL_CREDENTIALS_JSON")
        if env_json:
            credentials_path.write_text(env_json)
            print("Credentials ecrites depuis GMAIL_CREDENTIALS_JSON")
        else:
            print("\nFichier gmail_credentials.json introuvable.")
            print("Options :")
            print("  1. Telecharge-le depuis https://console.cloud.google.com/apis/credentials")
            print("  2. Place-le dans commercial-agent/config/gmail_credentials.json")
            print("  3. Ou definis la variable GMAIL_CREDENTIALS_JSON avec le contenu JSON")
            sys.exit(1)

    # Check for existing token
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.valid:
            print("Token Gmail deja valide !")
        elif creds and creds.expired and creds.refresh_token:
            print("Token expire, rafraichissement...")
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            print("Token rafraichi !")
        else:
            creds = None

    # New OAuth flow if needed
    if not creds:
        print("\n" + "=" * 50)
        print("  AUTORISATION GMAIL")
        print("  Un navigateur va s'ouvrir...")
        print("  Connecte-toi avec bp.thevenot@gmail.com")
        print("  et autorise l'acces.")
        print("=" * 50 + "\n")

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=8090)
        token_path.write_text(creds.to_json())
        print(f"\nToken sauvegarde dans {token_path}")

    # Verify it works
    print("\nVerification de la connexion Gmail...")
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print(f"Connecte a : {profile['emailAddress']}")
    print(f"Messages : {profile['messagesTotal']}")

    # Print token for Railway
    token_content = token_path.read_text()
    print("\n" + "=" * 50)
    print("  SETUP TERMINE !")
    print("=" * 50)
    print("\nPour Railway, ajoute cette variable d'environnement :")
    print("\nNom : GMAIL_TOKEN_JSON")
    print("Valeur :")
    print(token_content)
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
