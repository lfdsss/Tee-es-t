"""Script interactif pour coller les cles API dans le fichier .env."""

import os

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
ENV_EXAMPLE = os.path.join(os.path.dirname(__file__), ".env.example")


def main():
    print("\n" + "=" * 60)
    print("  CONFIGURATION DES CLES API")
    print("  Colle chaque cle quand demande (ou Enter pour passer)")
    print("=" * 60)

    # Load existing .env or create from example
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            env_content = f.read()
    elif os.path.exists(ENV_EXAMPLE):
        with open(ENV_EXAMPLE, "r") as f:
            env_content = f.read()
    else:
        env_content = ""

    keys = [
        {
            "name": "ANTHROPIC_API_KEY",
            "prompt": "1/5 — Cle Anthropic (sk-ant-...)",
            "placeholder": "sk-ant-...",
        },
        {
            "name": "HUBSPOT_API_KEY",
            "prompt": "2/5 — Token HubSpot Private App (pat-...)",
            "placeholder": "pat-...",
        },
        {
            "name": "NOTION_API_KEY",
            "prompt": "3/5 — Token Notion Integration (ntn_...)",
            "placeholder": "ntn_...",
        },
        {
            "name": "GITHUB_TOKEN",
            "prompt": "4/5 — Token GitHub (ghp_...)",
            "placeholder": "ghp_...",
        },
    ]

    updated = 0

    for key in keys:
        print(f"\n  {key['prompt']}")

        # Show current value (masked)
        current = _get_current_value(env_content, key["name"])
        if current and current != key["placeholder"]:
            masked = current[:8] + "..." + current[-4:] if len(current) > 12 else "***"
            print(f"  (actuel: {masked})")

        value = input("  → Colle la cle ici : ").strip()

        if value:
            env_content = _set_env_value(env_content, key["name"], value)
            updated += 1
            print(f"  ✓ {key['name']} enregistre")
        else:
            print("  — Passe")

    # Gmail credentials path
    print("\n  5/5 — Fichier Gmail credentials")
    gmail_path = "./config/gmail_credentials.json"
    if os.path.exists(gmail_path):
        print(f"  ✓ Fichier trouve : {gmail_path}")
    else:
        print(f"  Le fichier {gmail_path} n'existe pas encore.")
        print("  Telecharge-le depuis Google Cloud Console et place-le dans config/")
        custom = input("  Chemin personnalise (ou Enter pour garder le defaut) : ").strip()
        if custom:
            gmail_path = custom
            env_content = _set_env_value(env_content, "GMAIL_CREDENTIALS_PATH", gmail_path)

    # Write .env
    with open(ENV_FILE, "w") as f:
        f.write(env_content)

    print(f"\n{'=' * 60}")
    if updated > 0:
        print(f"  {updated} cle(s) enregistree(s) dans .env")
    else:
        print("  Aucune modification.")
    print("\n  Pour verifier : python -c \"from dotenv import load_dotenv; load_dotenv(); import os; print('Anthropic:', 'OK' if os.getenv('ANTHROPIC_API_KEY','').startswith('sk-') else 'MISSING')\"")
    print("\n  Pour lancer l'agent :")
    print("    python main.py              (mode interactif)")
    print("    python autonomous.py morning (mode autonome)")
    print(f"{'=' * 60}")


def _get_current_value(content: str, key: str) -> str:
    for line in content.split("\n"):
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def _set_env_value(content: str, key: str, value: str) -> str:
    lines = content.split("\n")
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
