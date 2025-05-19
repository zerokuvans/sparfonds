# Script para generar certificados SSL autofirmados para desarrollo
import os
import subprocess
import sys

def generar_certificados():
    print("Generando certificados SSL autofirmados para desarrollo...")
    
    # Verificar si OpenSSL está disponible
    try:
        subprocess.run(["openssl", "version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: OpenSSL no está disponible en el sistema.")
        print("Por favor, instale OpenSSL y asegúrese de que esté en el PATH del sistema.")
        return False
    
    # Crear directorio para certificados si no existe
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates")
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    # Rutas para los archivos de certificado y clave
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    
    # Verificar si los certificados ya existen
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("Los certificados ya existen en:", cert_dir)
        print("Si desea regenerarlos, elimine los archivos existentes primero.")
        return True
    
    # Generar certificado autofirmado
    try:
        # Generar clave privada y certificado en un solo comando
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", "-nodes",
            "-out", cert_path, "-keyout", key_path,
            "-days", "365", "-subj", "/CN=localhost"
        ], check=True)
        
        print("Certificados generados exitosamente en:", cert_dir)
        print("\nNOTA: Este es un certificado autofirmado para desarrollo.")
        print("En producción, debe usar certificados emitidos por una autoridad certificadora confiable.")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error al generar certificados: {e}")
        return False

if __name__ == "__main__":
    generar_certificados()