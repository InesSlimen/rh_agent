# Agent RH :

### Tool calling

`tool_calling_demo.py` est un script de démonstration des outils (tool calling) pour cet agent RH.
Il définit trois fonctions exposées à l'agent : `search_policy`, `create_ticket` et `send_email`, avec
leur description, leurs paramètres JSON Schema, et un contrôle de sécurité simple.

### Corporate Tools Server (MCP)

Ce dépôt contient un serveur de micro-outils d'entreprise basé sur le protocole **MCP (Model Context Protocol)** utilisant le framework **FastMCP**. Il expose des outils permettant à un agent d'intelligence artificielle de consulter les politiques RH, de créer des tickets de support informatique et d'envoyer des e-mails externes de manière sécurisée.

Le serveur intègre une politique de sécurité stricte (`TOOLS_SECURITY`) pour classifier les risques liés à l'exécution de chaque outil (notamment la validation humaine requise pour les actions critiques).

## 📋 Fonctionnalités et Matrice de Sécurité

Les outils sont configurés selon le niveau de risque suivant :

| Outil | Description | Type | Risque | Confirmation Requise |
| :--- | :--- | :--- | :--- | :--- |
| `search_policy` | Consulter les procédures internes RH | `READ` | **LOW** | ❌ Non |
| `create_ticket` | Créer un ticket support informatique | `WRITE` | **MEDIUM** | ❌ Non |
| `send_email` | Envoyer un e-mail externe | `SEND` | **HIGH** |  Oui (Human-in-the-loop) |

> ⚠️ **Sécurité :** Les métadonnées de sécurité sont injectées directement dans les descriptions des outils (`docstrings`) afin que l'agent IA ou le client MCP puisse intercepter et valider l'action avant son exécution.

### Tri et Analyse de CV

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

   **macOS / Linux :**
   ```bash
   python3 --version   # vérifier que la version est >= 3.11
   python3 -m venv env
   source env/bin/activate
   ```

   **Windows (PowerShell) :**
   ```powershell
   python --version   # vérifier que la version est >= 3.11
   python -m venv env
   .\env\Scripts\Activate.ps1
   ```

   **Windows (cmd) :**
   ```cmd
   python --version   :: vérifier que la version est >= 3.11
   python -m venv env
   env\Scripts\activate.bat
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copier le fichier d'exemple puis renseigner votre clé API Groq :

   **macOS / Linux :**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   **Windows (PowerShell) :**
   ```powershell
   Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```

   **Windows (cmd) :**
   ```cmd
   copy .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```

   Puis renseigner la clé dans `.streamlit/secrets.toml` :
   ```toml
   GROQ_API_KEY = "gsk_votre_cle_api_ici"
   ```

2. Ajouter les fiches de poste à comparer aux CV dans le dossier `fiches_de_poste/`, au format
   `.txt` (un fichier par fiche de poste). Des exemples sont déjà fournis.

## Lancer les applications


### 1. Démo Tool Calling (Chat avec outils et validation humaine)

```bash
streamlit run tool_calling_demo.py
```

L'interface de chat s'ouvre dans le navigateur (par défaut sur http://localhost:8501).

### 2. Corporate Tools Server (MCP)
```bash
python server.py
```
Dans un deuxième terminal :

```bash
python client.py
```

### 3. Application Tri et Analyse de CV

```bash
streamlit run analyse_cv.py
```

L'application s'ouvre automatiquement dans le navigateur (par défaut sur http://localhost:8501).

> **Premier lancement :** le modèle d'embedding (`paraphrase-multilingual-MiniLM-L12-v2`, ~470 Mo)
> est téléchargé et mis en cache localement — ça peut prendre quelques minutes selon la connexion.
> Les lancements suivants seront rapides.

## Utilisation

### Application Tri et analyse CV

1. Charger un CV au format PDF.
2. Cliquer sur **« Extraire le CV et chercher les fiches de poste correspondantes »** — le texte du CV est extrait et comparé (par similarité d'embeddings) aux fiches de poste du dossier `fiches_de_poste/`.
3. Choisir la fiche de poste la plus pertinente parmi les 3 propositions, puis lancer l'analyse LLM.
4. Consulter le score de pertinence, les compétences détectées et la synthèse générée par l'IA.
5. Valider ou rejeter la candidature, relire/modifier le brouillon d'email généré, puis l'envoyer.

### Démo Tool Calling (Test des outils)

Cette démo permet de tester la capacité de l'agent à appeler des fonctions et à demander une confirmation à l'utilisateur avant d'exécuter des actions critiques (comme l'envoi d'email).

Des exemples prêts à être copiés sont fournis dans la barre latérale gauche pour tester l'agent :

1. **Recherche de procédures (Lecture seule)** :
   Copiez/collez la phrase `Quelle est la règle de télétravail ?`. L'agent va exécuter automatiquement l'outil `search_policy` et vous répondre.
2. **Création de ticket support (Modification système)** :
   Copiez/collez la phrase `Crée un ticket support. Mon ordinateur ne démarre plus.`. L'agent va exécuter automatiquement l'outil `create_ticket` et afficher le numéro de ticket créé.
3. **Envoi d'email (Action critique nécessitant confirmation)** :
   Copiez/collez la phrase `Envoie un email au directeur pour signaler une panne serveur.`.
   - L'agent va suspendre l'exécution et afficher une demande de validation : **⚠️ Validation requise** avec les détails du mail.
   - Vous aurez le choix de cliquer sur **Oui, envoyer** (l'action est exécutée et l'email est envoyé) ou **Non, annuler** (l'action est annulée et l'agent s'adapte au refus).


