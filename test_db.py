from database import get_connection

conn = get_connection()

print("Koneksi Berhasil")

conn.close()