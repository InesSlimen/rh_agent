import os
import json
import asyncio
import streamlit as st
import uuid
from dotenv import load_dotenv
from groq import Groq


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))

# Configuration pour démarrer et communiquer avec le serveur MCP
server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

def mcp_to_groq_tools(mcp_tools):
    """Convertit le catalogue d'outils MCP vers le format attendu par Groq."""
    groq_tools = []
    for tool in mcp_tools:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        })
    return groq_tools

async def run_agent(user_message: str):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialisation de la connexion avec le serveur MCP
            await session.initialize()
            
            # Récupération et conversion des outils disponibles
            mcp_tools_response = await session.list_tools()
            groq_tools = mcp_to_groq_tools(mcp_tools_response.tools)

            messages = [
                {
                    "role": "system",
                    "content": "Tu es un agent IA d'entreprise. Tu utilises exclusivement les outils fournis via MCP."
                },
                {"role": "user", "content": user_message}
            ]

            while True:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=groq_tools,
                    tool_choice="auto",
                    temperature=0
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    print("\n[Agent] Réponse finale :")
                    print(message.content)
                    break

                messages.append(message)

                for call in message.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)

                    print(f"\n[Client] Appel d'outil détecté : {name}")
                    print(f"[Client] Arguments générés par le LLM : {args}")

                    # ------------------------------------------------------
                    # SÉCURITÉ DU CLIENT : LOGIQUE DE VALIDATION INTERCEPTÉE
                    # ------------------------------------------------------
                    if name == "send_email":
                        print("\n⚠️  [SÉCURITÉ] ACTION CRITIQUE DÉTECTÉE ⚠️")
                        print(f"Destinataire : {args.get('recipient')}")
                        print(f"Sujet        : {args.get('subject')}")
                        print(f"Message      : {args.get('body')}")
                        
                        confirm = input("\nAutorisez-vous l'envoi de cet email ? (oui/non) : ")
                        
                        if confirm.lower() != "oui":
                            print("❌ Action annulée par l'utilisateur.")
                            result_text = json.dumps({"status": "cancelled", "message": "Envoi annulé par l'opérateur humain."})
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": result_text
                            })
                            continue

                    # Injection automatique d'un request_id unique pour create_ticket s'il manque
                    if name == "create_ticket" and "request_id" not in args:
                        args["request_id"] = f"req_{uuid.uuid4().hex[:8]}"
                        print(f"[Client] Injecté request_id unique pour l'idempotence : {args['request_id']}")

                    # Appel effectif du serveur MCP
                    mcp_result = await session.call_tool(name, arguments=args)
                    result_text = mcp_result.content[0].text
                    print(f"[Client] Résultat brut du serveur : {result_text}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result_text
                    })

async def main():
    print("==================================================")
    print("TEST 1 : Outil de Lecture (search_policy)")
    print("==================================================")
    await run_agent("Bonjour, j'aimerais savoir quelle est notre politique concernant le télétravail s'il vous plaît ?")
    
    print("\n==================================================")
    print("TEST 2 : Outil d'Écriture (create_ticket)")
    print("==================================================")
    await run_agent("Mon écran secondaire ne s'allume plus du tout, crée un ticket pour l'informatique.")
    
    print("\n==================================================")
    print("TEST 3 : Outil Critique (send_email)")
    print("==================================================")
    await run_agent("Envoie un email à rh@company.com avec pour sujet 'Absence' et pour corps 'Je serai absent demain pour RDV médical'.")

if __name__ == "__main__":
    asyncio.run(main())