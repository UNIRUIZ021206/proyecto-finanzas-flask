# app/models.py
from flask_login import UserMixin

class User(UserMixin):
    """Modelo de Usuario para Flask-Login"""
    def __init__(self, id, nombre, correo, id_rol):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.id_rol = id_rol