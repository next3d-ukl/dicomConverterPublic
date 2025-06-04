# Navigiere ins Verzeichnis des Skripts
cd "$(dirname "$0")"

# Virtuelle Umgebung erstellen, falls nicht vorhanden
if [ ! -d ".venv" ]; then
  echo "🔧 Erstelle virtuelle Umgebung..."
  python3.10 -m venv .venv
fi

# Aktivieren
echo "⚙️  Aktiviere .venv..."
source .venv/bin/activate

# Requirements installieren
if [ -f "requirements.txt" ]; then
  echo "📦 Installiere Abhängigkeiten..."
  pip install -r requirements.txt
fi

# main.py ausführen
if [ -f "src/main.py" ]; then
  echo "🚀 Starte src/main.py..."
  python src/main.py
else
  echo "❌ src/main.py nicht gefunden!"
fi

# Terminal offen lassen
echo "✅ Fertig. Drücke [Enter] zum Schließen."
read