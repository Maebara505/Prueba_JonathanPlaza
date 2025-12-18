import os
import random
import time
import requests
import csv
import concurrent.futures
from fake_useragent import UserAgent

# --- CONFIGURACIÓN ---
# ¡IMPORTANTE! Reemplaza esto con tu SESSIONID real actualizado
SESSION_ID = "77976809109%3A0XsyWHfWiRfYy6%3A16%3AAYip9rF3OJIzbOzYolF5mK3cIe3U5x1CFOGOHIZqmA" 

def get_user_details(username, session_id):
    """
    Obtiene detalles detallados (Bio, Nombre, Métricas) de un usuario.
    """
    headers = {
        "authority": "www.instagram.com",
        "accept": "*/*",
        "referer": f"https://www.instagram.com/{username}/",
        "user-agent": UserAgent().random,
        'x-ig-app-id': '936619743392459',
        "x-requested-with": "XMLHttpRequest"
    }
    
    cookies = {'sessionid': session_id}
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {}).get('user', {})
            
            if not user_data: return None

            # Extracción de datos solicitados en el punto 2
            return {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'full_name': user_data.get('full_name', ''), # Nombre completo
                'biography': user_data.get('biography', '').replace('\n', ' '), # Bio (sin saltos de línea)
                'external_url': user_data.get('external_url', ''), # Link en la bio
                'follower_count': user_data.get('edge_followed_by', {}).get('count', 0),
                'following_count': user_data.get('edge_follow', {}).get('count', 0),
                'is_private': user_data.get('is_private', False),
                'is_verified': user_data.get('is_verified', False),
                'category': user_data.get('category_name', 'N/A') # Categoría (ej. Músico, Blog personal)
            }
    except Exception as e:
        # Los errores suelen ser por Rate Limit (bloqueo temporal)
        pass 
    
    return None

def analyze_profile_patterns(user_data):
    """
    PUNTO 3: Función de Análisis Productivo.
    Identifica patrones para clasificar al usuario automáticamente.
    """
    tags = []
    bio = user_data['biography'].lower()
    followers = user_data['follower_count']
    following = user_data['following_count']

    # 1. Detección de Potencial Comercial (Leads)
    keywords_business = ['ceo', 'founder', 'fundador', 'dueño', 'marketing', 'ventas', 'manager', 'gerente', 'co-founder']
    if any(keyword in bio for keyword in keywords_business) or user_data['external_url']:
        tags.append("Lead Comercial")

    # 2. Detección de Influencia
    if followers > 100000:
        tags.append("Macro-Influencer")
    elif 5000 <= followers <= 100000:
        tags.append("Micro-Influencer")
    elif 1000 <= followers < 5000:
        tags.append("Nano-Influencer")

    # 3. Detección de Posibles Bots / Spam
    # Patrón: Siguen a muchísimos (mas de 1500) pero tienen muy pocos seguidores (<100) y sin foto/bio
    if following > 1500 and followers < 100:
        tags.append("Posible Bot/Spam")
    
    # 4. Ratio de "Calidad"
    if followers > 0 and following > 0:
        ratio = followers / following
        if ratio > 2.0:
            tags.append("Alta Autoridad") # Tiene el doble de seguidores que seguidos

    if not tags:
        tags.append("Usuario Estándar")

    return ", ".join(tags)

def get_followers_usernames(target_username, session_id, limit=None):
    """
    Obtiene SOLO la lista de usernames (nombres de usuario) de los seguidores.
    Es más ligero que sacar toda la info de golpe.
    """
    target_info = get_user_details(target_username, session_id)
    if not target_info:
        print("Error: No se pudo acceder al perfil objetivo. Revisa el SessionID.")
        return [], None

    target_id = target_info['id']
    print(f"Objetivo: {target_username} (ID: {target_id}) - Total Seguidores: {target_info['follower_count']}")
    
    followers_usernames = []
    max_id = None
    
    # Headers específicos para la API de paginación
    headers = {
        'authority': 'www.instagram.com',
        'accept': '*/*',
        'referer': f'https://www.instagram.com/{target_username}/followers/',
        'user-agent': UserAgent().random,
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest',
    }
    cookies = {'sessionid': session_id}

    print("Recopilando lista de usernames...")
    
    while True:
        try:
            params = {'count': '50', 'search_surface': 'follow_list_page'}
            if max_id: params['max_id'] = max_id

            url = f'https://www.instagram.com/api/v1/friendships/{target_id}/followers/'
            response = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=15)
            
            if response.status_code != 200: break
            
            data = response.json()
            users = data.get('users', [])
            
            for user in users:
                followers_usernames.append(user.get('username'))
            
            print(f" -> Recolectados: {len(followers_usernames)}")

            if limit and len(followers_usernames) >= limit: break
            if not data.get('next_max_id'): break
            
            max_id = data.get('next_max_id')
            time.sleep(random.uniform(2, 4)) # Pausa para evitar bloqueo rápido

        except Exception as e:
            print(f"Error en paginación: {e}")
            break
            
    return followers_usernames, target_info

def process_batch(usernames, session_id):
    """
    Procesa un lote de usernames para sacar su BIO y detalles completos.
    """
    results = []
    
    # MODIFICACIÓN: Usamos enumerate para tener un contador (i)
    for i, username in enumerate(usernames):
        
        # MODIFICACIÓN: Imprimimos qué perfil estamos analizando AHORA MISMO
        print(f"   [Analizando] {i+1}/{len(usernames)}: {username} ...")
        
        # Pausa aleatoria para simular comportamiento humano
        time.sleep(random.uniform(0.2, 1.2)) 
        
        details = get_user_details(username, session_id)
        if details:
            # APLICAMOS EL PUNTO 3: ANÁLISIS
            analisis = analyze_profile_patterns(details)
            details['analisis_patron'] = analisis
            results.append(details)
        else:
            print(f"   [x] No se pudo leer perfil de: {username}")
            
    return results

def main():
    target_user = input("Usuario objetivo: ").strip()
    # PRECAUCIÓN: Instagram es muy estricto. Si pones hilos altos (más de 2) te bloquearán rápido.
    try:
        max_limit = int(input("¿Límite de seguidores a analizar? (0 para todos - Riesgoso): ") or 0)
    except:
        max_limit = 0
        
    if max_limit == 0: max_limit = None

    # 1. Obtener lista base de nombres
    usernames_list, target_info = get_followers_usernames(target_user, SESSION_ID, limit=max_limit)
    
    if not usernames_list:
        print("No se encontraron seguidores o hubo error de conexión.")
        return

    print(f"\nIniciando extracción profunda de {len(usernames_list)} perfiles...")
    print("NOTA: Esto tomará tiempo para evitar bloqueos de Instagram.")

    # 2. Procesamiento (Se recomienda 1 o 2 hilos máximo para extracción de detalles)
    # Dividimos la lista en chunks
    num_threads = 2 
    chunk_size = len(usernames_list) // num_threads if len(usernames_list) > num_threads else 1
    chunks = [usernames_list[i:i + chunk_size] for i in range(0, len(usernames_list), chunk_size)]
    
    final_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(process_batch, chunk, SESSION_ID) for chunk in chunks]
        
        for future in concurrent.futures.as_completed(futures):
            final_data.extend(future.result())

    # 3. Guardar CSV
    if final_data:
        filename = f"{target_user}_analisis_seguidores.csv"
        keys = ['username', 'full_name', 'biography', 'analisis_patron', 'follower_count', 'following_count', 'category', 'external_url', 'is_private', 'is_verified', 'id']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(final_data)
            
        print(f"\n[ÉXITO] Análisis guardado en: {filename}")
        print("Ejemplo de análisis encontrado:")
        print(f"Usuario: {final_data[0]['username']} | Patrón: {final_data[0]['analisis_patron']}")
    else:
        print("No se pudieron extraer detalles de los perfiles.")

if __name__ == "__main__":
    main()