import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def analizar_asistencia(nombre_archivo):
    try:
        df = pd.read_excel(nombre_archivo)
        total_inscritos = len(df)
        asistentes = df[df['isPresent'] == True]
        total_asistentes = len(asistentes)
        
        porcentaje_asistencia = (total_asistentes / total_inscritos) * 100 if total_inscritos > 0 else 0

        roles_comunes = asistentes['Rol principal'].value_counts().head(3).to_dict()
        carreras_comunes = asistentes['Investigador Carreras'].str.split(',').explode().str.strip().value_counts().head(3).to_dict()

        datos_para_llm = {
            'total_inscritos': total_inscritos,
            'total_asistentes': total_asistentes,
            'porcentaje_asistencia': f"{porcentaje_asistencia:.2f}%",
            'roles_comunes': roles_comunes,
            'carreras_comunes': carreras_comunes
        }
        
        # LLM usando la API de Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        A partir de los siguientes datos del evento de las Jornadas de Investigación, genera un informe conciso y fácil de leer.
        
        Datos: {datos_para_llm}
        
        El informe debe destacar los hallazgos más interesantes. Por ejemplo, la tasa de asistencia,
        quiénes son los participantes más comunes (roles y carreras).
        """
        
        print("Enviando datos al LLM para su análisis... (Esto tomará unos segundos)")
        
        response = model.generate_content(prompt)
        informe_generado = response.text
        return informe_generado
    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
    except Exception as e:
        return f"Ocurrió un error: {e}"

if __name__ == "__main__":
    nombre_del_excel = "asistencias.xlsx"
    informe = analizar_asistencia(nombre_del_excel)
    print("\n------------------\n")
    print("Informe Generado por IA:")
    print(informe)