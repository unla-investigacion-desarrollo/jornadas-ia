import pandas as pd
import google.generativeai as genai
import sys
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def analizar_asistencia_dinamico(nombre_archivo, pregunta_usuario):
    try:
        df = pd.read_excel(nombre_archivo)
        df_asistentes = df[df['isPresent'] == True]
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Tú eres un asistente de análisis de datos. Tu tarea es responder a la pregunta del usuario basándote en los datos de asistencia.

        Aquí está la pregunta del usuario: "{pregunta_usuario}"

        Aquí están los datos de los asistentes (la columna 'Investigador Carreras'):
        {df_asistentes['Investigador Carreras'].to_string()}

        Basándote en la pregunta y los datos, genera una respuesta clara y concisa. Si la pregunta es sobre una distribución o conteo, incluye los números o porcentajes exactos.
        """
        
        print("Enviando la pregunta y los datos al LLM para el análisis dinámico...")
        
        response = model.generate_content(prompt)
        informe_generado = response.text
        
        return informe_generado
            
    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
    except Exception as e:
        return f"Ocurrió un error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Se requiere una pregunta para el análisis.")
    else:
        pregunta_del_usuario = sys.argv[1]
        nombre_del_excel = "asistencias.xlsx"
        respuesta = analizar_asistencia_dinamico(nombre_del_excel, pregunta_del_usuario)
        print(respuesta)