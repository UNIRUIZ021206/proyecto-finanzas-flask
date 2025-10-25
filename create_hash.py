import bcrypt

# --- Escribe aquí la contraseña que quieres para tu admin ---
contrasena_plana = "admin123"
# -----------------------------------------------------------

print(f"Generando hash para la contraseña: '{contrasena_plana}'...")

# Codificamos la contraseña a bytes
contrasena_bytes = contrasena_plana.encode('utf-8')

# Generamos el hash (esto incluye una "sal" aleatoria)
hash_bytes = bcrypt.hashpw(contrasena_bytes, bcrypt.gensalt())

# Convertimos el hash a formato HEXADECIMAL para SQL Server
hash_hex = hash_bytes.hex()

print("\n--- ¡LISTO! ---")
print("Copia la siguiente línea completa (empieza con 0x):")
print("\n" + f"0x{hash_hex}")