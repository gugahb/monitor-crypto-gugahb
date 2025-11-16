import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_file):
        print("📋 Carregando .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("⚠️  Arquivo .env não encontrado!")

from src.handlers.price_monitor import lambda_handler

if __name__ == "__main__":
    
    print("🚀 Iniciando monitor de criptomoedas...")
    result = lambda_handler({}, {})
    print(f"✅ Resultado: {result}")
