import sys
import traceback
sys.path.append('.')
from server import app, post_checkout

def main():
    # Construct a realistic order payload
    # Let's check with product index 0 (which has quantity > 0 in local test)
    payload = {
        "carrito": {"0": 1},
        "entrega": {
            "metodo": "Retiro en local",
            "direccion": "",
            "observacion": ""
        },
        "pago": {
            "metodo": "Efectivo"
        }
    }
    
    print("Testing checkout inside request context...")
    with app.test_request_context(json=payload, base_url='http://localhost:5000/'):
        try:
            response = post_checkout()
            print("Status:", response.status)
            print("Response JSON:", response.get_json())
        except Exception as e:
            print("Checkout failed with exception:")
            traceback.print_exc()

if __name__ == "__main__":
    main()
