# Agent RH — Tri et Analyse de CV

Application Streamlit qui automatise le tri de CV : extraction du PDF, recherche de la fiche de poste
la plus pertinente (RAG local par embeddings), analyse et scoring par un LLM (Llama via l'API Groq),
puis génération d'un brouillon d'email de réponse.

## Prérequis

- Python 3.11 ou supérieur
- Une clé API Groq (gratuite) : https://console.groq.com/keys

## Installation

1. Se placer dans le dossier du projet :
   ```bash
   cd RH_Agent
   ```

2. Créer et activer un environnement virtuel (nécessite Python 3.11+) :
   ```bash
   python3 --version   # vérifier que la version est >= 3.11
   python3 -m venv env
   source env/bin/activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copier le fichier d'exemple puis renseigner votre clé API Groq :
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   ```toml
   GROQ_API_KEY = "gsk_votre_cle_api_ici"
   ```

2. Ajouter les fiches de poste à comparer aux CV dans le dossier `fiches_de_poste/`, au format
   `.txt` (un fichier par fiche de poste). Des exemples sont déjà fournis.

## Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur (par défaut sur http://localhost:8501).

> **Premier lancement :** le modèle d'embedding (`paraphrase-multilingual-MiniLM-L12-v2`, ~470 Mo)
> est téléchargé et mis en cache localement — ça peut prendre quelques minutes selon la connexion.
> Les lancements suivants seront rapides.

## Utilisation

1. Charger un CV au format PDF.
2. Cliquer sur **« Extraire le CV et chercher les fiches de poste correspondantes »** — le texte du
   CV est extrait et comparé (par similarité d'embeddings) aux fiches de poste du dossier
   `fiches_de_poste/`.
3. Choisir la fiche de poste la plus pertinente parmi les 3 propositions, puis lancer l'analyse LLM.
4. Consulter le score de pertinence, les compétences détectées et la synthèse générée par l'IA.
5. Valider ou rejeter la candidature, relire/modifier le brouillon d'email généré, puis l'envoyer.

