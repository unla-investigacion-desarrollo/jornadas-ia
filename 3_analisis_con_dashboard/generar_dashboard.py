import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def generar_dashboard_inteligente(nombre_archivo):
    try:
        df = pd.read_excel(nombre_archivo)
        asistentes = df[df['isPresent'] == True]
        
        # Se obtiene la estructura de los datos para el LLM.
        datos_para_llm = {
            "columnas_asistentes": list(asistentes.columns),
            "valores_unicos_roles": asistentes['Rol principal'].unique().tolist(),
            "valores_unicos_carreras": asistentes['Investigador Carreras'].str.split(',').explode().str.strip().unique().tolist()
        }

        prompt = f"""
        Actúa como un experto en visualización de datos. Analiza la estructura de los siguientes datos y propón un plan para generar 3 gráficos relevantes.

        Los datos de los asistentes al evento tienen esta estructura:
        {json.dumps(datos_para_llm, indent=3)}

        Propón los gráficos en un array JSON. Para cada objeto, incluye:
        - "titulo": Un título descriptivo.
        - "tipo_grafico": "bar" o "pie"
        - "eje_x": El nombre de la columna para el eje X (ej. "Rol principal").
        - "eje_y": La métrica para el eje Y (si aplica, ej. "cantidad").
        - "metrica": La operación para calcular los datos ("conteo").
        - "top_n": (Opcional) Un número entero para mostrar solo los N principales elementos si hay muchos (ej. 10).

        Ejemplo de formato JSON esperado:
        [
          {{
            "titulo": "Distribución de Roles Principales",
            "tipo_grafico": "bar",
            "eje_x": "Rol principal",
            "eje_y": "cantidad",
            "metrica": "conteo",
            "top_n": 5
          }},
          {{
            "titulo": "Proporción de Carreras de Asistentes",
            "tipo_grafico": "pie",
            "eje_x": "Investigador Carreras",
            "eje_y": "cantidad",
            "metrica": "conteo",
            "top_n": 7
          }}
          etc...
        ]
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)

        try:
            propuestas_json_str = response.text.replace('```json', '').replace('```', '')
            propuestas_de_graficos = json.loads(propuestas_json_str)
        except json.JSONDecodeError:
            print("Error: La IA no devolvió un JSON válido. Usando gráficos por defecto.")
            propuestas_de_graficos = [
                {"titulo": "Distribución de Roles Principales (Por Defecto)", "tipo_grafico": "bar", "eje_x": "Rol principal", "eje_y": "cantidad", "metrica": "conteo", "top_n": 10},
                {"titulo": "Proporción de Carreras (Por Defecto)", "tipo_grafico": "pie", "eje_x": "Investigador Carreras", "eje_y": "cantidad", "metrica": "conteo", "top_n": 10}
            ]

        # Se generan los gráficos dinámicamente
        html_output = "<html><head><title>Dashboard Dinámico</title></head><body>"
        html_output += "<h1>Dashboard generado por IA</h1>"
        html_output += "<p>Los siguientes gráficos fueron propuestos y generados por un agente de IA.</p>"
        
        for propuesta in propuestas_de_graficos:
            if propuesta['metrica'] == 'conteo' and 'eje_x' in propuesta:
                columna_analisis = propuesta['eje_x']
                
                if columna_analisis in asistentes.columns and asistentes[columna_analisis].dtype == 'object' and asistentes[columna_analisis].str.contains(',', na=False).any():
                    df_grafico = asistentes[columna_analisis].str.split(',').explode().str.strip().value_counts().reset_index()
                elif columna_analisis in asistentes.columns:
                    df_grafico = asistentes[columna_analisis].value_counts().reset_index()
                else:
                    print(f"Advertencia: Columna '{columna_analisis}' no encontrada o no es adecuada para el conteo. Saltando gráfico.")
                    continue # Salta este gráfico si la columna no es válida
                
                df_grafico.columns = [columna_analisis, 'cantidad']
                
                # Aplicar top_n si está especificado
                if 'top_n' in propuesta and isinstance(propuesta['top_n'], int) and propuesta['top_n'] > 0:
                    df_grafico = df_grafico.head(propuesta['top_n'])

                fig = None
                if propuesta['tipo_grafico'] == 'bar':
                    fig = px.bar(
                        df_grafico, 
                        x=columna_analisis, 
                        y='cantidad', 
                        title=propuesta['titulo'],
                        color=columna_analisis
                    )
                elif propuesta['tipo_grafico'] == 'pie':
                    fig = px.pie(
                        df_grafico, 
                        names=columna_analisis,
                        values='cantidad',
                        title=propuesta['titulo']
                    )
                
                if fig:
                    html_output += fig.to_html(full_html=False, include_plotlyjs='cdn')

        html_output += "</body></html>"
        
        with open('dashboard_dinamico.html', 'w') as f:
            f.write(html_output)

        print("Dashboard generado exitosamente en dashboard_dinamico.html")
        print("Abriendo el dashboard en tu navegador...")
        os.system("start dashboard_dinamico.html") if os.name == 'nt' else os.system("open dashboard_dinamico.html")
        
    except FileNotFoundError:
        print(f"Error: El archivo '{nombre_archivo}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    generar_dashboard_inteligente("asistencias.xlsx")