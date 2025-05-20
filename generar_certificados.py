# Script para generar certificados SSL autofirmados para desarrollo
import os
import subprocess
import sys

def generar_certificados(forzar=False):
    print("Generando certificados SSL autofirmados para SparFonds...")
    
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
        if forzar:
            print("Eliminando certificados existentes para regenerarlos...")
            try:
                os.remove(cert_path)
                os.remove(key_path)
                print("Certificados eliminados correctamente.")
            except Exception as e:
                print(f"Error al eliminar certificados existentes: {e}")
                return False
        else:
            print("Los certificados ya existen en:", cert_dir)
            print("Si desea regenerarlos, ejecute el script con la opción --forzar")
            return True
    
    # Generar certificado autofirmado
    try:
        # Generar clave privada y certificado en un solo comando con datos de SparFonds
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", "-nodes",
            "-out", cert_path, "-keyout", key_path,
            "-days", "365", "-subj", "/C=ES/ST=Madrid/L=Madrid/O=SparFonds/OU=Desarrollo/CN=sparfonds.local"
        ], check=True)
        
        print("Certificados SSL para SparFonds generados exitosamente en:", cert_dir)
        print("\nNOTA: Este es un certificado autofirmado específico para SparFonds en entorno de desarrollo.")
        print("En producción, debe usar certificados emitidos por una autoridad certificadora confiable.")
        print("\nDetalles del certificado:")
        print(" - Organización: SparFonds")
        print(" - Nombre común: sparfonds.local")
        print(" - Validez: 365 días")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error al generar certificados: {e}")
        return False

if __name__ == "__main__":
    # Verificar si se pasó el argumento --forzar
    forzar = "--forzar" in sys.argv
    generar_certificados(forzar)