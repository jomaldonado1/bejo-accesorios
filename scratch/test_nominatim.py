import requests

def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {
        'User-Agent': 'BEJO_Accesorios_App/1.0 (tienda_accesorios_agent)'
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            address = data.get("display_name", "")
            # Limpiar un poco la dirección para que no sea tan larga
            address_parts = data.get("address", {})
            road = address_parts.get("road", "")
            house_number = address_parts.get("house_number", "")
            city = address_parts.get("city", address_parts.get("town", address_parts.get("suburb", "")))
            state = address_parts.get("state", "")
            
            clean_addr = ""
            if road:
                clean_addr += road
                if house_number:
                    clean_addr += f" {house_number}"
                if city:
                    clean_addr += f", {city}"
                if state:
                    clean_addr += f", {state}"
            else:
                clean_addr = address
                
            return clean_addr
        return f"Error: {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

def main():
    # Coordenadas de prueba en San Miguel de Tucumán (cerca de la plaza independencia)
    lat, lon = -26.8306, -65.2201
    print("Geocodificando coordinates:", lat, lon)
    addr = reverse_geocode(lat, lon)
    print("Dirección obtenida:", addr)

if __name__ == "__main__":
    main()
