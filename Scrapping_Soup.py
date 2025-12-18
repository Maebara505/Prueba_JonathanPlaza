import pandas as pd
import requests
from collections import Counter
import re

# ==========================================
# CONFIGURACIÓN GLOBAL
# ==========================================
# URL objetivo: Lista completa de frases en latín de Wikipedia
URL = "https://en.wikipedia.org/wiki/List_of_Latin_phrases_(full)"
# Nombre del archivo donde se guardarán los resultados
ARCHIVO_SALIDA = "todas_las_frases.xlsx"


def scrapear_todo_pandas():
    """
    Descarga todas las tablas de la URL simulando ser un navegador real.
    """
    print(f"Conectando a {URL}...")
    print("Esto puede tardar un poco porque la página 'full' es gigante...")
    
    try:
        # --- CORRECCIÓN ANTI-BLOQUEO (ERROR 403) ---
        # 1. Definimos un 'User-Agent' para parecer un navegador real (Chrome)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 2. Usamos requests con los headers para bajar el HTML primero
        response = requests.get(URL, headers=headers)
        response.raise_for_status() # Verifica si hubo error (404, 500, etc)
        
        # 3. Le pasamos el TEXTO descargado a Pandas (no la URL directa)
        # Esto engaña a Wikipedia porque ya bajamos el contenido como "navegador"
        tablas = pd.read_html(response.text, match="Latin", header=0)
        
        print(f"¡Se encontraron {len(tablas)} tablas de frases!")
        
        # Unimos todas las tablas
        df_completo = pd.concat(tablas, ignore_index=True)
        
        if 'Latin' in df_completo.columns and 'Translation' in df_completo.columns:
            df_final = df_completo[['Latin', 'Translation']].dropna()
            return df_final
        else:
            print("Error: Las columnas no se llaman 'Latin' y 'Translation'.")
            return None

    except Exception as e:
        print(f"Error grave durante el scraping: {e}")
        return None

def analisis_y_guardado(df):
    """
    Guarda el DataFrame en Excel y realiza un análisis de frecuencia de palabras.

    Args:
        df (pd.DataFrame): El dataframe con los datos limpios.

    Returns:
        list: Lista con las 5 palabras más comunes en inglés.
    """
    if df is None: return

    # --- GUARDAR EXCEL ---
    print(f"Guardando {len(df)} frases en Excel...")
    # index=False evita que se guarde la columna de números de fila (0,1,2...) en el Excel
    df.to_excel(ARCHIVO_SALIDA, index=False)
    
    # --- ANÁLISIS DE FRECUENCIA ---
    print("\n--- Analizando palabras ---")
    
    def limpiar_y_contar(texto_columna):
        """Función auxiliar para procesar texto y contar palabras."""
        # Convierte toda la columna a un solo string gigante
        texto = " ".join(texto_columna.astype(str))
        
        # EXPRESIÓN REGULAR (REGEX):
        # \b        : Borde de palabra (para no cortar palabras a la mitad)
        # [a-zA-Z]  : Solo letras (ignora números y puntuación)
        # {4,}      : Mínimo 4 letras (filtra conectores cortos como 'in', 'at', 'et')
        palabras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower()) 
        
        # Counter crea un diccionario tipo {'palabra': numero_veces}
        return Counter(palabras).most_common(5)

    # Aplicamos el análisis a ambas columnas
    top_latin = limpiar_y_contar(df['Latin'])
    # Nota: En la wiki completa la columna suele llamarse 'Translation' en lugar de 'English'
    top_ingles = limpiar_y_contar(df['Translation']) 

    print("Top 5 palabras en Latín:", top_latin)
    print("Top 5 palabras en Inglés:", top_ingles)
    
    # Retorna solo las palabras (sin el conteo numérico) para usarlas en las frases
    return [p[0] for p in top_ingles] 

def generar_nuevas_frases(palabras):
    """
    Genera oraciones en español insertando dinámicamente las palabras clave encontradas.

    Args:
        palabras (list): Lista de palabras clave en inglés.
    """
    print("\n--- 5 Frases Nuevas (Español) ---")
    
    # Plantillas de oraciones donde {} será reemplazado por una palabra
    plantillas = [
        "El principio de '{}' define nuestra ética moderna.",
        "Sin '{}', no existiría la justicia verdadera.",
        "A través de la historia, '{}' ha sido la clave del poder.",
        "La filosofía antigua se resume en el concepto de '{}'.",
        "Debemos aspirar siempre a '{}' en nuestras vidas."
    ]
    
    # Lógica de seguridad: Si hay menos de 5 palabras, rellenamos con "vida" para evitar error
    while len(palabras) < 5: 
        palabras.append("vida")
        
    for i in range(5):
        # .format() sustituye los corchetes {} por la palabra correspondiente
        print(f"{i+1}. {plantillas[i].format(palabras[i])}")

# ==========================================
# PUNTO DE ENTRADA (MAIN)
# ==========================================
if __name__ == "__main__":
    # Paso 1: Obtener datos
    df = scrapear_todo_pandas()
    
    # Paso 2: Analizar y Guardar
    palabras_top = analisis_y_guardado(df)
    
    # Paso 3: Generar contenido nuevo (solo si hubo éxito en el paso anterior)
    if palabras_top:
        generar_nuevas_frases(palabras_top)