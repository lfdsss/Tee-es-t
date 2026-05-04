"""Ouvre automatiquement toutes les pages pour creer les cles API dans Chrome."""

import webbrowser
import time

PAGES = [
    {
        "name": "1. ANTHROPIC — Cle API Claude",
        "url": "https://console.anthropic.com/settings/keys",
        "instructions": "Clique 'Create Key' → copie la cle sk-ant-...",
    },
    {
        "name": "2. HUBSPOT — Private App Token",
        "url": "https://app-eu1.hubspot.com/private-apps/147714071",
        "instructions": "Clique 'Create a private app' → nom: Agent Commercial → Scopes: coche tout CRM → Create → copie le token pat-...",
    },
    {
        "name": "3. NOTION — Integration interne",
        "url": "https://www.notion.so/profile/integrations",
        "instructions": "Clique 'New integration' → nom: Agent Commercial → Submit → copie le token ntn_...",
    },
    {
        "name": "4. GITHUB — Personal Access Token",
        "url": "https://github.com/settings/tokens/new?scopes=repo,write:issues&description=Agent+Commercial+L-FDS",
        "instructions": "Le formulaire est pre-rempli. Clique 'Generate token' → copie ghp_...",
    },
    {
        "name": "5. GOOGLE CLOUD — Gmail API Credentials",
        "url": "https://console.cloud.google.com/apis/credentials",
        "instructions": "Cree un projet 'Agent Commercial' → Active Gmail API → Create Credentials → OAuth 2.0 → Desktop App → Telecharge le JSON",
    },
]


def main():
    print("\n" + "=" * 60)
    print("  OUVERTURE DES PAGES POUR CREER LES CLES API")
    print("=" * 60)

    # Try to use Chrome specifically
    chrome_paths = [
        "google-chrome",
        "google-chrome-stable",
        "/usr/bin/google-chrome",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]

    browser = None
    for path in chrome_paths:
        try:
            browser = webbrowser.get(f"{path} %s")
            break
        except webbrowser.Error:
            continue

    if browser is None:
        browser = webbrowser  # Fallback to default browser

    for i, page in enumerate(PAGES):
        print(f"\n{'─' * 60}")
        print(f"  {page['name']}")
        print(f"  URL: {page['url']}")
        print(f"  → {page['instructions']}")
        print(f"{'─' * 60}")

        if hasattr(browser, 'open'):
            browser.open(page["url"])
        else:
            browser.open_new_tab(page["url"])

        if i < len(PAGES) - 1:
            time.sleep(1.5)  # Small delay between tabs

    print(f"\n{'=' * 60}")
    print("  5 onglets ouverts dans Chrome !")
    print("")
    print("  Une fois les cles copiees, lance :")
    print("    python fill_env.py")
    print("  pour les coller dans le fichier .env")
    print("=" * 60)


if __name__ == "__main__":
    main()
