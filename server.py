import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

app = FastMCP("Corporate-Tools-Server")
tickets = {}

# Votre dictionnaire reste déclaré globalement dans le script
TOOLS_SECURITY = {
    "search_policy": {"type": "READ", "risk": "LOW", "confirmation": False},
    "create_ticket": {"type": "WRITE", "risk": "MEDIUM", "confirmation": False},
    "send_email": {"type": "SEND", "risk": "HIGH", "confirmation": True}
}

def write_log(tool: str, args: dict, result: dict):
    log = {"time": str(datetime.now()), "tool": tool, "arguments": args, "result": result}
    with open("agent_logs.json", "a", encoding="utf8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

@app.tool()
def search_policy(topic: str) -> str:
    """Consulter les procédures internes RH.
    [SECURITY: TYPE=READ, RISK=LOW, CONFIRMATION=FALSE]"""
    policies = {
        "congé": "Chaque employé possède 25 jours de congés annuels.",
        "télétravail": "Le télétravail est autorisé 2 jours par semaine."
    }
    result = {"topic": topic, "information": policies.get(topic.lower(), "Aucune procédure trouvée.")}
    write_log("search_policy", {"topic": topic}, result)
    return json.dumps(result, ensure_ascii=False)

@app.tool()
def create_ticket(title: str, description: str, request_id: str) -> str:
    """Créer un ticket support informatique.
    [SECURITY: TYPE=WRITE, RISK=MEDIUM, CONFIRMATION=FALSE]"""
    if request_id in tickets:
        return json.dumps({"status": "already_exists", "ticket_id": tickets[request_id]})
    ticket_id = len(tickets) + 1000
    tickets[request_id] = ticket_id
    result = {"status": "created", "ticket_id": ticket_id, "title": title}
    write_log("create_ticket", {"title": title, "description": description, "request_id": request_id}, result)
    return json.dumps(result, ensure_ascii=False)

@app.tool()
def send_email(recipient: str, subject: str, body: str) -> str:
    """Envoyer un email externe (Outil critique).
    [SECURITY: TYPE=SEND, RISK=HIGH, CONFIRMATION=TRUE]"""
    result = {"status": "sent", "recipient": recipient, "message": "Email envoyé avec succès"}
    write_log("send_email", {"recipient": recipient, "subject": subject, "body": body}, result)
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    app.run(transport="stdio")