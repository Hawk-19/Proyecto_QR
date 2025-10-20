import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.qr_generador import generar_qr

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_QR_DIR = os.path.join(BASE_DIR, "backend", "static", "qr_code")
LOGOS_DIR = os.path.join(BASE_DIR, "backend", "static", "logos")

# --- Montar carpetas estáticas ---
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "backend", "static")),
    name="static"
)
app.mount(
    "/frontend",
    StaticFiles(directory=os.path.join(BASE_DIR, "frontend")),
    name="frontend"
)

# --- Aqui se maneja el error 404 personalizado ---
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        file_path = os.path.join(BASE_DIR, "frontend", "404.html")
        if os.path.exists(file_path):
            return FileResponse(file_path, status_code=404)
        else:
            return HTMLResponse(
                content="<h1>404 - Página no encontrada</h1><a href='/'>Volver al inicio</a>",
                status_code=404
            )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )

# --- Aqui se genera los QRs por carpeta ---
@app.on_event("startup")
def startup_event():
    print("BASE_DIR:", BASE_DIR)
    print("LOGOS_DIR:", LOGOS_DIR)
    print("LOGOS existentes:", os.listdir(LOGOS_DIR) if os.path.exists(LOGOS_DIR) else "NO EXISTE")
    os.makedirs(STATIC_QR_DIR, exist_ok=True)
    docs_dir = os.path.join(BASE_DIR, "docs")
    try:
        if not os.path.exists(docs_dir):
            print(f"La carpeta {docs_dir} no existe, se omite la generación de QRs.")
            return
        for folder in os.listdir(docs_dir):
            folder_path = os.path.join(docs_dir, folder)
            doc_path = os.path.join(folder_path, "documento.pdf")
            if os.path.isdir(folder_path) and os.path.exists(doc_path):
                qr_path = os.path.join(STATIC_QR_DIR, f"{folder}.png")
                doc_url = f"http://proyecto-qr-1-vq6l.onrender.com/documento/{folder}"
                # Logo específico por carpeta
                logo_path = os.path.join(LOGOS_DIR, f"{folder.lower()}.png")
                if not os.path.exists(logo_path):
                    logo_path = None  # Si no existe, se genera sin logo
                try:
                    generar_qr(doc_url, qr_path, logo_path)
                except Exception as e:
                    print(f"Error generando QR para {folder}: {e}")
    except Exception as e:
        print(f"Error al acceder a {docs_dir}: {e}")

# --- Servir documento por nombre de carpeta ---
@app.get("/documento/{nombre}")
async def serve_documento(nombre: str):
    doc_path = os.path.join(BASE_DIR, "docs", nombre, "documento.pdf")
    try:
        if os.path.exists(doc_path):
            return FileResponse(
                path=doc_path,
                media_type="application/pdf",
                filename="documento.pdf",
                headers={"Content-Disposition": "inline; filename=documento.pdf"}
            )
        return Response(content="Documento no encontrado", status_code=404)
    except Exception as e:
        return Response(content=f"Error al acceder al documento: {e}", status_code=500)

# --- Listar QRs disponibles en Frontend ---
@app.get("/qr/list")
def list_qrs():
    try:
        if not os.path.exists(STATIC_QR_DIR):
            return JSONResponse(content={"documentos": []})
        nombres = [
            os.path.splitext(f)[0]
            for f in os.listdir(STATIC_QR_DIR)
            if f.endswith(".png")
        ]
        return JSONResponse(content={"documentos": nombres})
    except Exception as e:
        return JSONResponse(content={"error": f"Error listando QRs: {e}"}, status_code=500)

# --- Servir QR por nombre de carpeta ---
@app.get("/qr/{nombre}")
async def serve_qr(nombre: str):
    try:
        qr_path = os.path.join(STATIC_QR_DIR, f"{nombre}.png")
        if os.path.exists(qr_path):
            return FileResponse(qr_path, media_type="image/png")
        return Response(content="QR no encontrado", status_code=404)
    except Exception as e:
        return Response(content=f"Error al acceder al QR: {e}", status_code=500)

# --- Descargar QR ---
@app.get("/qr/{nombre}/download")
async def download_qr(nombre: str):
    try:
        qr_path = os.path.join(STATIC_QR_DIR, f"{nombre}.png")
        if os.path.exists(qr_path):
            return FileResponse(
                qr_path,
                media_type="image/png",
                filename=f"{nombre}_QR.png",
                headers={"Content-Disposition": f'attachment; filename="{nombre}_QR.png"'}
            )
        return Response(content="QR no encontrado", status_code=404)
    except Exception as e:
        return Response(content=f"Error al descargar el QR: {e}", status_code=500)

# --- Aqui se muestra el Index.html ---
@app.get("/")
def serve_frontend():
    file_path = os.path.join(BASE_DIR, "frontend", "index.html")
    try:
        if os.path.exists(file_path):
            return FileResponse(file_path)
        return Response(content="index.html no encontrado", status_code=404)
    except Exception as e:
        return Response(content=f"Error al cargar el frontend: {e}", status_code=500)
