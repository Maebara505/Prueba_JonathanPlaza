import pandas as pd
import requests
from collections import Counter
import re
import sys

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
ARCHIVO_SALIDA = "resultados_examen.xlsx"

def scrapear_interactivo():
    """
    Pide una URL, descarga todas las tablas y devuelve la más grande encontrada.
    """
    print("\n--- PASO 1: CONEXIÓN ---")
    
    # --- CAMBIO IMPORTANTE: Bucle para obligar a meter una URL ---
    url = ""
    while True:
        try:
            # print explícito para asegurar que se vea el mensaje
            print(">>> Por favor, PEGA la URL de Wikipedia y presiona ENTER:")
            url = input().strip() # input limpio
            
            if len(url) > 0:
                break # Si hay texto, salimos del bucle y continuamos
            else:
                print("⚠️  No detecté la URL. Inténtalo de nuevo (Ctrl+V y Enter).")
                print("------------------------------------------------")
        except EOFError:
            pass

    print(f"\nConectando a: {url} ...")
    
    try:
        # Headers para evitar bloqueo 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tablas = pd.read_html(response.text, match=".+", header=0)
        
        if not tablas:
            print("❌ No se encontraron tablas en esa página.")
            return None
            
        print(f"✅ ¡Se encontraron {len(tablas)} tablas!")
        
        # Tomamos la tabla más grande
        tabla_principal = sorted(tablas, key=lambda x: len(x), reverse=True)[0]
        
        print(f"Seleccionada automáticamente la tabla con {len(tabla_principal)} filas.")
        return tabla_principal

    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return None

def seleccionar_columnas(df):
    """
    Muestra las columnas disponibles y pide al usuario elegir 2 por índice.
    """
    if df is None: return None
    
    print("\n--- PASO 2: SELECCIÓN DE COLUMNAS ---")
    print("He encontrado estas columnas:")
    
    columnas = df.columns.tolist()
    for i, col in enumerate(columnas):
        print(f"[{i}] {col}")
        
    print("------------------------------------------------")
    print("Selecciona los números de las columnas (Ej: 0 y 1)")
    
    while True:
        try:
            print(">>> Escribe el número de la Columna 1 (Principal):")
            entrada1 = input().strip()
            if not entrada1.isdigit(): continue # Si no es numero, repite
            idx_1 = int(entrada1)

            print(">>> Escribe el número de la Columna 2 (Secundaria):")
            entrada2 = input().strip()
            if not entrada2.isdigit(): continue 
            idx_2 = int(entrada2)
            
            # Verificamos validez
            if idx_1 >= len(columnas) or idx_2 >= len(columnas):
                print("⚠️  Error: Número de columna no existe. Mira la lista de arriba.")
                continue

            # Procesamos
            df_seleccionado = df.iloc[:, [idx_1, idx_2]].copy()
            df_seleccionado.columns = ['Columna_A', 'Columna_B']
            return df_seleccionado.dropna()
            
        except Exception as e:
            print(f"Error: {e}, intenta de nuevo.")

def analisis_y_guardado(df):
    """
    Guarda en Excel y cuenta palabras frecuentes.
    """
    if df is None: return []

    print(f"\n--- PASO 3: GUARDADO ---")
    try:
        df.to_excel(ARCHIVO_SALIDA, index=False)
        print(f"✅ Archivo guardado correctamente: {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"❌ Error al guardar Excel (CIERRA EL ARCHIVO SI LO TIENES ABIERTO): {e}")
        return []
    
    print("\n--- PASO 4: ANÁLISIS DE PALABRAS ---")
    
    def obtener_top_5(texto_columna):
        texto = " ".join(texto_columna.astype(str))
        palabras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower())
        return Counter(palabras).most_common(5)

    top_A = obtener_top_5(df['Columna_A'])
    top_B = obtener_top_5(df['Columna_B'])

    print(f"Top frecuentes en Columna 1: {top_A}")
    print(f"Top frecuentes en Columna 2: {top_B}")
    
    return [p[0] for p in top_B]

def generar_frases_genericas(palabras):
    """
    Genera frases de relleno.
    """
    print("\n--- PASO 5: FRASES NUEVAS ---")
    
    plantillas = [
        "El análisis indica que '{}' es un factor determinante.",
        "En este contexto, '{}' resalta por su frecuencia.",
        "La relación con '{}' es fundamental para comprender la tabla.",
        "Se observa una tendencia clara hacia el concepto de '{}'.",
        "Resulta interesante notar la repetición de '{}' en los datos."
    ]
    
    while len(palabras) < 5: palabras.append("dato")
        
    for i in range(5):
        print(f"{i+1}. {plantillas[i].format(palabras[i])}")

# ==============================================================================
# EJECUCIÓN
# ==============================================================================
if __name__ == "__main__":
    df_crudo = scrapear_interactivo()
    
    if df_crudo is not None:
        df_limpio = seleccionar_columnas(df_crudo)
        
        if df_limpio is not None:
            palabras_clave = analisis_y_guardado(df_limpio)
            if palabras_clave:
                generar_frases_genericas(palabras_clave)
        else:
            print("Fin por error en selección.")
    else:
        # Aquí el programa termina suavemente si falla la descarga
        pass