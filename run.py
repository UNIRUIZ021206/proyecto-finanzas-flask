# run.py
from app import create_app
from livereload import Server

# 1. Creamos la aplicación llamando a la fábrica
app = create_app()

if __name__ == '__main__':
    # 2. Configuramos el servidor LiveReload
    server = Server(app.wsgi_app)
    
    # 3. Le decimos a LiveReload qué archivos vigilar
    # Vigila los archivos principales de la app
    server.watch('app/__init__.py')
    server.watch('app/utils.py')
    server.watch('app/models.py')
    server.watch('app/extensions.py')
    
    # Vigila las rutas de todos los blueprints
    server.watch('app/auth/routes.py')
    server.watch('app/admin/routes.py')
    server.watch('app/analysis/routes.py')
    server.watch('app/main/routes.py')
    
    # Vigila todos los templates y archivos estáticos
    server.watch('app/templates/*.html') 
    server.watch('app/static/*.css') # Los CSS están directamente en app/static/
    
    print("Iniciando servidor en http://127.0.0.1:5000")
    
    # 4. Iniciamos el servidor
    server.serve(port=5000, host='127.0.0.1', debug=True)