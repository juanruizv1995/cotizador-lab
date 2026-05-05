from fastapi import FastAPI
from supabase import create_client
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
cliente_groq = Groq(api_key=GROQ_KEY)

app = FastAPI()

@app.get("/")
def read_root():
    return {"mensaje": "¡Hola desde el cotizador de laboratorio!"}
    

@app.get("/servicios")
def obtener_servicios():
    response = supabase.table("servicios").select("*").execute()
    return response.data


@app.post("/cotizar")
def cotizar(mensaje: str):
    servicios = supabase.table("servicios").select("*").execute().data
    print("SERVICIOS:", servicios)  # ← agrega esta línea
    lista_servicios = "\n".join([f"- {s['nombre']}: ${s['precio']} COP" for s in servicios])
    print("LISTA:", lista_servicios)  # ← y esta
    prompt = f"""
    Eres un asistente de cotizaciones para un laboratorio de metrología.
    
    Los servicios disponibles con sus precios son:
    {lista_servicios}
    
    El cliente envió este mensaje: "{mensaje}"
    
    Instrucciones:
    1. Identifica qué servicios solicita el cliente comparándolos con la lista
    2. Usa EXACTAMENTE los precios de la lista
    3. Calcula el total multiplicando precio_unitario por cantidad
    4. Responde ÚNICAMENTE con el JSON, sin texto adicional
    
    Formato de respuesta:
    {{"servicios": [{{"servicios": [{{"nombre": "nombre exacto del servicio", "cantidad": 1, "precio_unitario": 150000, "total": 150000}}], "total_general": 0}}
    """
    respuesta = cliente_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"cotizacion": respuesta.choices[0].message.content}



@app.post("/whatsapp")
async def whatsapp(request: Request):
    form = await request.form()
    mensaje = form.get("Body", "")
    
    # Consultar servicios de Supabase
    servicios = supabase.table("servicios").select("*").execute().data
    lista_servicios = "\n".join([f"- {s['nombre']}: ${s['precio']} COP" for s in servicios])
    
    prompt = f"""
    Eres un asistente de cotizaciones para un laboratorio de metrología.
    
    Los servicios disponibles con sus precios son:
    {lista_servicios}
    
    El cliente envió este mensaje: "{mensaje}"
    
    Responde con un mensaje de WhatsApp amigable que incluya:
    - Saludo breve
    - Lista de servicios solicitados con cantidades y precios
    - Total general
    - Despedida
    
    Usa los precios EXACTOS de la lista. Formato de precios: $150.000 COP
    
    Escribe al final , te quiero mucho mi amorcito 
    """
    
    respuesta = cliente_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    texto = respuesta.choices[0].message.content
    
    resp = MessagingResponse()
    resp.message(texto)
    return PlainTextResponse(str(resp), media_type="application/xml")


#venv\Scripts\activate
#uvicorn main:app --reload