Hier ist ein konkreter Task‑Plan, der die in meinem Bericht beschriebenen Optimierungen Schritt für Schritt umsetzt. Er ist modular aufgebaut, sodass Sie die Maßnahmen je nach Priorität kombinieren können.

1. **Evaluationsmetriken einführen**

   * Legen Sie für jede Mission eine klare Erfolgsmetrik fest (z. B. Anzahl abgeschlossener Teilaufgaben, Fehleranzahl, Qualitätsbewertung des Ergebnisses). Der Self‑Loop‑Prompt betont, dass pro Loop nur „ein sinnvoller Fortschrittsschritt“ ausgeführt werden soll – diese Metrik sollte messen, ob dieser Schritt das Ziel voranbringt.
   * Entwickeln Sie eine Funktion, die nach jedem Loop den aktuellen Wert dieser Metrik ermittelt und im `context_packet` speichert. So kann der Fortschritt später verglichen werden.

2. **Adaptive Steuerung der LLM‑Parameter implementieren**

   * Passen Sie Temperatur, `max_tokens` und Anzahl der Schritte an die Ergebnisse an. Wenn die Metriken stagnieren oder sich verschlechtern, erhöhen Sie z. B. die Temperatur, um explorativere Antworten zu erzwingen; bei Erfolgen senken Sie sie, um fokussierter zu arbeiten.
   * Fügen Sie eine Logik hinzu, die diese Parameter in der `LoopConfig` dynamisch aktualisiert, bevor der Prompt für den nächsten Loop erstellt wird.

3. **Loop‑State erweitern und persistieren**

   * Der aktuelle `loop_state` speichert nur Iteration, History‑Summary, offene Fragen und Constraints. Implementieren Sie eine Funktion, die nach jedem Loop eine prägnante Zusammenfassung erstellt (Liste der Aktionen, Ergebnisse, offene Probleme) und diese im State ablegt.
   * Speichern Sie außerdem offene Fragen und neue Constraints, damit der LLM‑Call im nächsten Loop gezielt darauf eingehen kann.
   * Legen Sie eine Versionierung an: Speichern Sie den State nach jedem Loop als JSON‑Datei. So können Sie Lernschritte nachverfolgen und später auswerten.

4. **PDF‑Extraktion als neuen Action‑Typ integrieren**

   * Entwickeln Sie einen Tool‑Action‑Handler `pdf_to_json`, der PDF‑Dateien liest und deren Inhalt als strukturiertes JSON ausgibt. Dies ermöglicht es dem LLM, externe Dokumente in die Analyse einzubeziehen.
   * Ergänzen Sie die Job‑Planungslogik (`call_llm_for_plan`), sodass diese Aktion vorgeschlagen werden kann, wenn PDF‑Dateien im Projekt gefunden werden.

5. **Simulations‑Modus für Tests erstellen**

   * Die jetzige Implementierung ruft die LLM‑Schnittstelle über `LLMClient.call` auf. Implementieren Sie in `LLMClient` einen alternativen Modus, der deterministische Antworten liefert (z. B. Listen von Dateien, simple Pläne), um die Loop‑Logik ohne externes LLM testen zu können.
   * Variieren Sie die Simulation leicht, um die adaptive Parametersteuerung zu testen.

6. **Robustes Parsing und Fehlerbehandlung**

   * Der Prompt für Folgejobs verlangt strikt gültiges JSON. Ergänzen Sie einen Parser, der JSON auch aus unstrukturiertem Text extrahieren kann, um fehlerhafte LLM‑Antworten zu retten.
   * Verbessern Sie das Error‑Handling: Der Loop‑Runner schaltet derzeit bei zu vielen Fehlern in den Safe‑Mode. Implementieren Sie in diesem Modus diagnostische Schritte (z. B. Code‑Linting, Log‑Analyse) und passt den Prompt an, statt nur abzubrechen.

7. **Persistente Lernschritte und Visualisierung**

   * Legen Sie nach jedem Loop einen „Lernschritt“ als JSON-Version an, die Datum, Iteration, wichtige Erkenntnisse und die Veränderung der Metrik enthält. Dies kann später über ein Dashboard visualisiert werden.
   * Fügen Sie eine Funktion hinzu, die diese Lernschritte zusammenfasst und an das Team reportet, um menschliches Feedback in die Optimierung einzubeziehen.

8. **Dokumentation und Tests**

   * Dokumentieren Sie jede neue Komponente (Evaluationsfunktion, adaptive Steuerung, PDF‑Extractor usw.) in README‑Dateien.
   * Schreiben Sie Unit‑ und Integrationstests für die neuen Funktionen, insbesondere für die adaptive Parameterlogik und das Parsing.

Durch diesen Task‑Plan werden die Self‑Loops nicht nur formale Konsistenz wahren, sondern auch systematisch aus ihren Ergebnissen lernen, sich anpassen und externe Informationen verarbeiten – der Kern einer effizienten evolutionären Architektur.
