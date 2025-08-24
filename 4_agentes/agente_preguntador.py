import pandas as pd
import google.generativeai as genai
import sys
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def generar_preguntas_relevantes(nombre_archivo, num_preguntas=3):
    try:
        df = pd.read_excel(nombre_archivo)
        columnas_disponibles = ", ".join(df.columns)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Actúa como un analista de datos. Tu tarea es generar {num_preguntas} preguntas relevantes, interesantes y específicas que se puedan responder analizando un archivo de Excel con las siguientes columnas: {columnas_disponibles}.

        Las preguntas deben estar orientadas a entender el perfil de los asistentes, la participación, y otros datos clave del evento. No respondas a las preguntas, solo genéralas.
        
        Ejemplos de preguntas relevantes:
        - ¿Cuál es el rol principal con mayor representación entre los asistentes?
        - ¿Qué porcentaje de los inscritos realmente asistió al evento?
        """
        
        response = model.generate_content(prompt)
        preguntas_generadas = response.text
        return preguntas_generadas.strip().split('\n')
    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
    except Exception as e:
        print(f"Error en el Agente Preguntador: {e}")
        return []

if __name__ == "__main__":
    nombre_del_excel = "asistencias.xlsx"
    
    print("Agente de PREGUNTAS: Pidiendo al Agente que genere 3 preguntas relevantes...")
    preguntas = generar_preguntas_relevantes(nombre_del_excel)
    
    print("\n--------------------------------------------------\n")
    print("El Agente ha generado las siguientes preguntas:")
    for i, p in enumerate(preguntas):
        print(f" {p.strip()}")
        
    print("\n--------------------------------------------------\n")
    
    for i, pregunta in enumerate(preguntas):
        if(pregunta != ""):
            print(f"Enviando la pregunta al Agente de ANALISIS Y RESPUESTA...")
            
            proceso = subprocess.run(
                [sys.executable, "4_agentes/agente_analisis_respuesta.py", pregunta.strip()], 
                capture_output=True, 
                text=True
            )
            respuesta = proceso.stdout.strip()
            print(f"\nPregunta: {pregunta}")
            print(f"Respuesta del Agente Analista: {respuesta}\n")