## jornadas-ia

🚀 Ejemplo de diferentres asistentes inteligente para Jornadas de Investigación del DDPyT UNLa (4ta Edición)
Este proyecto demuestra varios sistemas de agentes (multi-agente en algunos casos) de Inteligencia Artificial.

# Tecnologías Utilizadas

- Python: Lenguaje de programación principal para el desarrollo de los agentes.

- Google Gemini API: Modelo de Lenguaje Grande (LLM) para análisis de texto, detección de relevancia, extracción de preguntas y generación de respuestas/propuestas de gráficos.

- Gmail API: Para la lectura y envío de correos electrónicos.

- Pandas: Librería de Python para el análisis y manipulación de datos de Excel.

- Plotly Express: Librería de Python para la creación de gráficos interactivos y dashboards HTML.

# Librerias
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-generativeai pandas openpyxl python-docx plotly python-dotenv
```

# Configuración del Proyecto en Google Cloud

Configuración de Google Cloud Project (API de Gmail y OAuth 2.0)
Para que tu script pueda interactuar con Gmail, debes configurar un proyecto en Google Cloud Console:

1. Crea un Proyecto:

- Ve a [Google Cloud Console](https://console.developers.google.com/).

-  Crea un nuevo proyecto (ej. "AsistenteJornadasUNLa").

2. Habilita la API de Gmail:

- Sigue los pasos en [Developers Google Quickstart With Python](https://developers.google.com/workspace/gmail/api/quickstart/python) para la habilitación (modo Interno, para Externo se siguen otros pasos)

- Nota: En la sección "Usuarios de prueba", añade tu dirección de correo electrónico de G Suite. Esto es CRÍTICO para que la autenticación funcione mientras la aplicación no esté "publicada".


# Configuración de variables de entorno y archivos necesarios

1. API Key de Google Gemini

- Obtén tu API Key en [Google AI Studio](https://aistudio.google.com/app/apikey).

- Crea una clave API.

- Crea un archivo .env (En la misma carpeta de tu proyecto, crea un archivo llamado .env)

- Dentro de este archivo, añade la siguiente línea, reemplazando TU_API_KEY_AQUÍ con tu clave de Gemini:

```bash
GENAI_API_KEY=TU_API_KEY_AQUÍ
```

(El script usa python-dotenv para cargar esta clave de forma segura).

2. Configuración de la Ruta del Documento de Jornadas
Abre tu script 5_agente_integrado_gmail/agente_gmail.py y actualiza la variable RUTA_DOCUMENTO_JORNADAS con la ruta absoluta de tu archivo Word (.docx) que contiene la información de las jornadas.

```bash
RUTA_DOCUMENTO_JORNADAS = "/ruta/completa/a/tu/documento/info_jornadas_unla.docx"
```

5. Archivos de Credenciales y Token
credentials.json: Debe ser el archivo que descargaste de Google Cloud Console.

token.json: Este archivo se generará automáticamente la primera vez que te autentiques. Si cambias los SCOPES o la configuración de OAuth en Google Cloud, DEBES ELIMINAR token.json para forzar una nueva autenticación.

# Scripts

```bash
python3 1_analisis_simple/simple.py

python3 2_analisis_dinamico/dinamico.py "Dame un resumen de participantes al evento" (texto de ejemplo)

python3 3_analisis_con_dashboard/generar_dashboard.py

python3 4_agentes/agente_preguntador.py

python3 5_agente_integrado_gmail/agente_gmail.py
```