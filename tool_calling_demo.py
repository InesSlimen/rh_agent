import json
import streamlit as st
from datetime import datetime
from groq import Groq


# ======================================================
# 1. Connexion Groq
# ======================================================

client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))


# ======================================================
# 2. Catalogue des outils
# ======================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Consulter les procédures internes RH. Cet outil est uniquement en lecture. Il ne modifie aucune donnée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Sujet recherché dans les procédures"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Créer un ticket support informatique. Cet outil modifie le système et retourne un identifiant de ticket. Il est important de vérifier que la demande est valide et que les informations sont complètes avant de l'utiliser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "request_id": {"type": "string", "description": "Identifiant unique pour éviter les doublons"}
                },
                "required": ["title", "description", "request_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Envoyer un email externe. Outil critique : Une validation humaine obligatoire est nécessaire avant exécution. Ne jamais appeler automatiquement cet outil sans confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    }
]


# ======================================================
# 3. Implémentation Python des outils
# ======================================================

def search_policy(topic):
    policies = {
        "congé": "Chaque employé possède 25 jours de congés annuels.",
        "télétravail": "Le télétravail est autorisé 2 jours par semaine.",
        "sécurité": "Les mots de passe doivent être changés tous les 90 jours."
    }
    result = policies.get(topic.lower(), "Aucune procédure trouvée.")
    return {"topic": topic, "information": result}


tickets = {}


def create_ticket(title, description, request_id):
    if request_id in tickets:
        return {"status": "already_exists", "ticket_id": tickets[request_id]}
    ticket_id = len(tickets) + 1000
    tickets[request_id] = ticket_id
    return {"status": "created", "ticket_id": ticket_id, "title": title}


def send_email(recipient, subject, body):
    return {"status": "sent", "recipient": recipient, "message": "Email envoyé avec succès"}


# ======================================================
# 4. Sécurité des outils
# ======================================================

TOOLS_SECURITY = {
    "search_policy": {"type": "READ", "risk": "LOW", "confirmation": False},
    "create_ticket": {"type": "WRITE", "risk": "MEDIUM", "confirmation": False},
    "send_email": {"type": "SEND", "risk": "HIGH", "confirmation": True}
}

available_functions = {
    "search_policy": search_policy,
    "create_ticket": create_ticket,
    "send_email": send_email,
}


# ======================================================
# 5. Logging
# ======================================================

def write_log(tool, args, result):
    log = {
        "time": str(datetime.now()),
        "tool": tool,
        "arguments": args,
        "result": result,
    }
    with open("agent_logs.json", "a", encoding="utf8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")


def execute_tool(name, args, bypass_confirmation=False):
    security = TOOLS_SECURITY.get(name)
    if security is None:
        return {"error": "Outil interdit"}

    if security["confirmation"] and not bypass_confirmation:
        return {
            "status": "cancelled",
            "message": "Action nécessitant confirmation humaine non disponible dans cette interface."
        }

    try:
        result = available_functions[name](**args)
        write_log(name, args, result)
        return result
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        write_log(name, args, error)
        return error


# ======================================================
# 6. Agent Tool Calling (Stateful)
# ======================================================

def run_agent_loop():
    while True:
        # 1. Vérifier s'il y a des appels d'outils non répondus dans le dernier message assistant
        last_assistant_msg = None
        last_assistant_idx = -1
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            msg = st.session_state.messages[i]
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            if role == "assistant":
                tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
                if tool_calls:
                    last_assistant_msg = msg
                    last_assistant_idx = i
                    break
            elif role == "user":
                break

        unanswered_calls = []
        if last_assistant_msg:
            tool_calls = getattr(last_assistant_msg, "tool_calls", None) or last_assistant_msg.get("tool_calls", [])
            answered_call_ids = set()
            for msg in st.session_state.messages[last_assistant_idx + 1:]:
                role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
                if role == "tool":
                    call_id = getattr(msg, "tool_call_id", None) or msg.get("tool_call_id")
                    if call_id:
                        answered_call_ids.add(call_id)
            
            for call in tool_calls:
                call_id = getattr(call, "id", None) or (call.get("id") if isinstance(call, dict) else None)
                if call_id not in answered_call_ids:
                    unanswered_calls.append(call)

        if unanswered_calls:
            has_pending = False
            for call in unanswered_calls:
                call_id = getattr(call, "id", None) or (call.get("id") if isinstance(call, dict) else None)
                func = getattr(call, "function", None) or call.get("function")
                name = getattr(func, "name", None) or (func.get("name") if isinstance(func, dict) else None)
                args_str = getattr(func, "arguments", None) or (func.get("arguments") if isinstance(func, dict) else None)
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
                
                security = TOOLS_SECURITY.get(name, {"confirmation": False})
                if security["confirmation"]:
                    # Pause pour confirmation humaine
                    st.session_state.pending_tool_call = {
                        "call_id": call_id,
                        "name": name,
                        "arguments": args
                    }
                    has_pending = True
                    break
                else:
                    # Exécuter l'outil automatique
                    result = execute_tool(name, args)
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                    st.session_state.chat_history.append({
                        "role": "tool",
                        "tool": name,
                        "args": args,
                        "result": result
                    })
            if has_pending:
                return
            else:
                continue

        # 2. Aucun appel d'outil en attente de réponse, appeler le LLM
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto",
            temperature=0,
        )
        message = response.choices[0].message

        if not getattr(message, "tool_calls", None):
            assistant_text = message.content.strip() if message.content else ""
            if assistant_text:
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_text})
            return

        st.session_state.messages.append(message)


def chat(user_message):
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": """
Tu es un agent IA d'entreprise.

Tu peux utiliser uniquement les outils fournis.

Règles :
- search_policy : lecture uniquement.
- create_ticket : modification du système.
- send_email : nécessite toujours confirmation humaine.

Ne jamais inventer un résultat.
Si un outil échoue, explique clairement l'erreur.
"""
            }
        ]
    
    st.session_state.messages.append({"role": "user", "content": user_message})
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    run_agent_loop()


def render_chat_event(event):
    if event["role"] == "user":
        if hasattr(st, "chat_message"):
            with st.chat_message("user"):
                st.write(event["content"])
        else:
            st.markdown(f"**Utilisateur :** {event['content']}")
    elif event["role"] == "assistant":
        if hasattr(st, "chat_message"):
            with st.chat_message("assistant"):
                st.write(event["content"])
        else:
            st.markdown(f"**Assistant :** {event['content']}")
    else:
        st.markdown(
            f"**Outil `{event['tool']}`**\n- Arguments : `{json.dumps(event['args'], ensure_ascii=False)}`\n- Résultat : `{json.dumps(event['result'], ensure_ascii=False)}`"
        )


def render_chat_interface():
    st.set_page_config(page_title="Tool Calling Demo", layout="wide")
    st.title("💬 Démo Chat - Tool Calling")
    st.write("Utilisez ce chat pour tester les outils `search_policy`, `create_ticket` et `send_email`.")

    # Exemples de messages à tester dans la barre latérale (Sidebar)
    with st.sidebar:
        st.header("💡 Exemples à tester")
        st.write("Copiez l'un des exemples ci-dessous pour le coller dans le chat :")
        
        st.write("**Exemple 1 : Règle de télétravail**")
        st.code("Quelle est la règle de télétravail ?", language="text")
        
        st.write("**Exemple 2 : Créer un ticket**")
        st.code("Crée un ticket support. Mon ordinateur ne démarre plus.", language="text")
        
        st.write("**Exemple 3 : Envoyer un email**")
        st.code("Envoie un email au directeur pour signaler une panne serveur.", language="text")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": """
Tu es un agent IA d'entreprise.

Tu peux utiliser uniquement les outils fournis.

Règles :
- search_policy : lecture uniquement.
- create_ticket : modification du système.
- send_email : nécessite toujours confirmation humaine.

Ne jamais inventer un résultat.
Si un outil échoue, explique clairement l'erreur.
"""
            }
        ]

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Votre message", placeholder="Exemple : Cherche la règle de télétravail.")
        submitted = st.form_submit_button("Envoyer")

    if submitted and user_input and user_input.strip():
        st.session_state.pending_tool_call = None
        with st.spinner("Envoi du message au modèle..."):
            chat(user_input.strip())

    if st.button("Réinitialiser le chat"):
        st.session_state.chat_history = []
        st.session_state.messages = [
            {
                "role": "system",
                "content": """
Tu es un agent IA d'entreprise.

Tu peux utiliser uniquement les outils fournis.

Règles :
- search_policy : lecture uniquement.
- create_ticket : modification du système.
- send_email : nécessite toujours confirmation humaine.

Ne jamais inventer un résultat.
Si un outil échoue, explique clairement l'erreur.
"""
            }
        ]
        st.session_state.pending_tool_call = None
        st.rerun()

    for event in st.session_state.chat_history:
        render_chat_event(event)

    # Affichage des boutons de confirmation s'il y a une action en attente
    if st.session_state.get("pending_tool_call"):
        pending = st.session_state.pending_tool_call
        st.warning(f"⚠️ **Validation requise** : L'agent souhaite exécuter l'action `{pending['name']}`.")
        
        args = pending["arguments"]
        if pending["name"] == "send_email":
            st.info(f"**Destinataire :** {args.get('recipient')}\n\n**Objet :** {args.get('subject')}\n\n**Corps du message :**\n{args.get('body')}")
        else:
            st.json(args)
            
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Oui, envoyer", key="confirm_yes", type="primary"):
                name = pending["name"]
                args = pending["arguments"]
                call_id = pending["call_id"]
                
                # Exécuter l'outil (bypass de la sécurité puisqu'il y a confirmation humaine)
                result = execute_tool(name, args, bypass_confirmation=True)
                
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
                st.session_state.chat_history.append({
                    "role": "tool",
                    "tool": name,
                    "args": args,
                    "result": result
                })
                
                st.session_state.pending_tool_call = None
                with st.spinner("Poursuite de la conversation..."):
                    run_agent_loop()
                st.rerun()
                
        with col2:
            if st.button("Non, annuler", key="confirm_no"):
                name = pending["name"]
                args = pending["arguments"]
                call_id = pending["call_id"]
                
                # Résultat d'annulation
                result = {
                    "status": "cancelled",
                    "message": "Action annulée par l'utilisateur."
                }
                write_log(name, args, result)
                
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
                st.session_state.chat_history.append({
                    "role": "tool",
                    "tool": name,
                    "args": args,
                    "result": result
                })
                
                st.session_state.pending_tool_call = None
                with st.spinner("Poursuite de la conversation..."):
                    run_agent_loop()
                st.rerun()


# ======================================================
# 7. Interface graphique
# ======================================================


if __name__ == "__main__":
    try:
        render_chat_interface()
    except Exception:
        print("Lancez ce script avec Streamlit : streamlit run tool_calling_demo.py")
