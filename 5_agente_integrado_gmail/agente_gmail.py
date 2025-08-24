import os.path
import os
import base64
import email
from datetime import date
import time
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
from docx import Document
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

RUTA_DOCUMENTO_JORNADAS = "info_jornadas_unla.docx"
HOST = '127.0.0.1'
PORT = 8080

def obtener_servicio_gmail():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=PORT, host=HOST)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    service = build("gmail", "v1", credentials=creds)
    return service

def decodificar_cuerpo_mail(msg_obj):
    mail_text = ""
    if msg_obj.is_multipart():
        for part in msg_obj.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    mail_text = part.get_payload(decode=True).decode()
                    break
                except UnicodeDecodeError:
                    mail_text = part.get_payload(decode=True).decode('latin-1')
                    break
    else:
        if msg_obj.get_content_type() == 'text/plain':
            try:
                mail_text = msg_obj.get_payload(decode=True).decode()
            except UnicodeDecodeError:
                mail_text = part.get_payload(decode=True).decode('latin-1')
    return mail_text.strip()

def enviar_mail_respuesta(servicio_gmail, destinatario, asunto_original, respuesta_ia):
    try:
        message = EmailMessage()
        message['To'] = destinatario
        message['From'] = 'me'
        message['Subject'] = f"RE: {asunto_original} - Respuesta sobre Jornadas UNLa (IA)"
        message.set_content(respuesta_ia, charset='utf-8')        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        enviado = servicio_gmail.users().messages().send(
            userId='me', 
            body={'raw': raw_message}
        ).execute()
        
        print(f"  [MAIL]: Respuesta enviada a {destinatario} (ID del mensaje: {enviado['id']})")
        return True
    except HttpError as error:
        print(f"  [MAIL]: Error al enviar el correo a {destinatario}: {error}")
        return False
    except Exception as e:
        print(f"  [MAIL]: Ocurrió un error inesperado al enviar el correo: {e}")
        return False

def leer_documento_word(ruta_documento):
    try:
        documento = Document(ruta_documento)
        texto_completo = []
        for paragraph in documento.paragraphs:
            texto_completo.append(paragraph.text)
        return "\n".join(texto_completo)
    except FileNotFoundError:
        print(f"Error: El documento '{ruta_documento}' no fue encontrado.")
        return None
    except Exception as e:
        print(f"Ocurrió un error al leer el documento de Word: {e}")
        return None

def analizar_relevancia_con_gemini(texto_mail, asunto_mail, remitente_mail):
    """
    Usa Gemini para determinar si un correo se relaciona con "Jornadas de Investigación de la UNLa, en su 4ta edición"
    y si contiene una pregunta.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Analiza el siguiente correo electrónico. Dime EXCLUSIVAMENTE "SÍ" si se relaciona claramente con las "Jornadas de Investigación de la UNLa, en su 4ta edición" Y si contiene una pregunta. Si no se relaciona, no contiene una pregunta o tienes dudas, dime EXCLUSIVAMENTE "NO".

    ---
    Remitente: {remitente_mail}
    Asunto: {asunto_mail}
    Cuerpo del Correo:
    {texto_mail}
    ---
    """
    
    try:
        print("  [IA]: Analizando relevancia y pregunta en el correo...")
        response = model.generate_content(prompt)
        respuesta_ia = response.text.strip().upper()
        return respuesta_ia == "SÍ"
    except Exception as e:
        print(f"  [IA]: Error al analizar relevancia con Gemini: {e}")
        return False

def extraer_pregunta_del_mail(texto_mail, asunto_mail):
    """
    Usa Gemini para extraer la pregunta específica de un correo relevante.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Del siguiente correo electrónico, extrae la pregunta más clara y directa que se relacione
    con las "Jornadas de Investigación de la UNLa, en su 4ta edición".
    Responde EXCLUSIVAMENTE con la pregunta extraída, sin rodeos.
    Si hay múltiples preguntas, elige la principal.

    ---
    Asunto: {asunto_mail}
    Cuerpo del Correo:
    {texto_mail}
    ---
    """
    try:
        print("  [IA]: Extrayendo pregunta del correo...")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  [IA]: Error al extraer pregunta con Gemini: {e}")
        return "No se pudo extraer una pregunta clara."


def sugerir_respuesta_con_gemini(pregunta_extraida, texto_documento_jornadas, contexto_mail):
    """
    Usa la API de Gemini para sugerir una respuesta combinando la pregunta del mail
    con la información del documento de las jornadas.
    """
    if not texto_documento_jornadas:
        return "No se pudo cargar la información de las jornadas para sugerir una respuesta."

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Eres un asistente de comunicación de las "Jornadas de Investigación de la UNLa, en su 4ta edición".
    Has recibido la siguiente pregunta de un asistente por correo electrónico: "{pregunta_extraida}".

    El correo original tenía el siguiente contexto:
    ---
    {contexto_mail}
    ---

    Aquí tienes información oficial de las Jornadas (documento):
    ---
    {texto_documento_jornadas}
    ---

    Genera una respuesta clara, concisa, profesional y útil para el asistente,
    basándote EXCLUSIVAMENTE en la información disponible en el documento oficial de las Jornadas
    para responder a su pregunta. Si la información no está en el documento, indica amablemente
    que no se encuentra allí o sugiere dónde podría encontrarla si es posible.
    """
    
    try:
        print("  [IA]: Generando respuesta sugerida con Gemini (usando el documento)...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al generar la respuesta sugerida con Gemini: {e}"

def main():
  print("--- Iniciando Asistente Inteligente de Jornadas UNLa ---")
  print(f"Cargando información del documento de las jornadas desde '{RUTA_DOCUMENTO_JORNADAS}'...")
  texto_doc_jornadas = leer_documento_word(RUTA_DOCUMENTO_JORNADAS)
  if not texto_doc_jornadas:
      print("No se pudo cargar el documento de las jornadas. El asistente no podrá responder preguntas sobre él.")
      return

  try: 
    # 1. Conectar a Gmail
    servicio_gmail = obtener_servicio_gmail()
    if not servicio_gmail:
        print("No se pudo conectar a Gmail. Revisa las credenciales.")
        return
    print("Conectado a Gmail exitosamente.")

    # 2. Filtrar correos del día de hoy
    today = date.today()
    query_date = today.strftime("%Y/%m/%d")
    gmail_query = f"after:{query_date}" 

    print(f"\nBuscando correos recibidos hoy ({query_date})...")
    
    messages_response = servicio_gmail.users().messages().list(userId='me', q=gmail_query, labelIds=['INBOX']).execute()
    messages = messages_response.get('messages', [])

    if not messages:
      print("No se encontraron correos recibidos hoy.")
      return

    print(f"Se encontraron {len(messages)} correos recibidos hoy. Analizando uno por uno...")
    
    correos_con_preguntas_relevantes = []

    for i, message in enumerate(messages):
        print(f"\n--- Analizando Correo {i+1}/{len(messages)} ---")
        
        msg_id = message['id']
        msg_raw_data = servicio_gmail.users().messages().get(userId='me', id=msg_id, format='raw').execute()
        
        raw_decoded_string = base64.urlsafe_b64decode(msg_raw_data['raw']).decode('utf-8', errors='ignore')
        msg_obj = email.message_from_string(raw_decoded_string)
        
        subject = msg_obj['Subject'] if 'Subject' in msg_obj and msg_obj['Subject'] else 'Sin asunto'
        sender = msg_obj['From'] if 'From' in msg_obj and msg_obj['From'] else 'Desconocido'
        # Extraer solo la dirección de correo del remitente
        remitente_email_address = email.utils.parseaddr(sender)[1]
        print(f"De: {sender}")
        print(f"Asunto: {subject}")
        cuerpo_texto = decodificar_cuerpo_mail(msg_obj)
        if cuerpo_texto:
            # --- AGENTE DE RELEVANCIA Y DETECCIÓN DE PREGUNTA ---
            es_relevante_y_pregunta = analizar_relevancia_con_gemini(cuerpo_texto, subject, sender)
            if es_relevante_y_pregunta:
                print("  => ¡Correo RELEVANTE con una pregunta sobre las Jornadas!")
                # --- AGENTE DE EXTRACCIÓN DE PREGUNTA ---
                pregunta_extraida = extraer_pregunta_del_mail(cuerpo_texto, subject)
                print(f"  [IA]: Pregunta extraída: '{pregunta_extraida}'")
                # --- AGENTE DE SUGERENCIA DE RESPUESTA ---
                respuesta_sugerida = sugerir_respuesta_con_gemini(
                    pregunta_extraida,
                    texto_doc_jornadas,
                    f"Remitente: {sender}\nAsunto: {subject}\nCuerpo: {cuerpo_texto[:500]}..." # Contexto breve del mail
                )
                # --- AGENTE DE ENVÍO AUTOMÁTICO DE RESPUESTA ---
                print("\n  [IA]: Intentando enviar respuesta automática...")
                envio_exitoso = enviar_mail_respuesta(
                    servicio_gmail, 
                    remitente_email_address, 
                    subject, 
                    respuesta_sugerida
                )
                correos_con_preguntas_relevantes.append({
                    'id': msg_id,
                    'remitente': sender,
                    'asunto': subject,
                    'pregunta': pregunta_extraida,
                    'respuesta_sugerida_ia': respuesta_sugerida,
                    'envio_automatico_exitoso': envio_exitoso
                })
            else:
                print("  => No relevante o no contiene una pregunta clara sobre las Jornadas.")
        else:
            print("  No se pudo extraer el cuerpo del correo en formato de texto plano para analizar.")
        # Pausa para evitar exceder límites de API, especialmente si hay muchos correos
        time.sleep(1) 

    print("\n\n--- INFORME FINAL DE MAILS CON PREGUNTAS RELEVANTES ---")
    if correos_con_preguntas_relevantes:
        print(f"Se encontraron {len(correos_con_preguntas_relevantes)} correos hoy con preguntas relevantes:")
        for correo in correos_con_preguntas_relevantes:
            print(f"\n------------------------------------")
            print(f"ID del Correo: {correo['id']}")
            print(f"De: {correo['remitente']}")
            print(f"Asunto: {correo['asunto']}")
            print(f"Pregunta Detectada por IA: {correo['pregunta']}")
            print(f"Respuesta Sugerida por IA (desde documento):\n{correo['respuesta_sugerida_ia']}")
            print(f"Envío Automático: {'Éxito' if correo['envio_automatico_exitoso'] else 'Fallido'}")
            print("------------------------------------")
    else:
        print("No se encontraron correos hoy con preguntas relevantes sobre las Jornadas de Investigación.")
  except HttpError as error:
    print(f"Ocurrió un error con la API de Gmail: {error}")
  except Exception as e:
      print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
  main()