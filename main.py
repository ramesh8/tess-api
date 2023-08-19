from typing import Union
from fastapi import FastAPI, UploadFile, File, Response
from fastapi.responses import StreamingResponse, FileResponse
import zipfile
import os
import aiofiles
import io
from io import StringIO
import traceback
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import sys

app = FastAPI()
CHUNK_SIZE = 1024 * 1024
tempdir = "/tmp/files/"

@app.get("/")
def read_root():
    return {"message": "Welcome to Tesseract OCR API"}

def searchq(text, query):
    if text.lower().find(query.lower()) != -1:
        return True
    return False


@app.post("/filterpdf/")
async def filterpdf(q:str, file:UploadFile, response:Response):
    
    if file.content_type in ["application/zip", "application/x-zip-compressed"]:
        extpath = os.path.join(f'./{tempdir}/{file.filename}/')
        try:
            with zipfile.ZipFile(io.BytesIO(await file.read()), 'r') as zip:
                zip.extractall(extpath)
            pdffile = list(Path(extpath).rglob("*.pdf"))
            if len(pdffile) > 0:
                pages = convert_from_path(pdffile[0])
                plist = []
                for i,page in enumerate(pages):
                    # page.save(f'{extpath}/pages/page{i}.jpeg','JPEG') # dont save on disk.
                    # send it to tesseract
                    text = pytesseract.image_to_string(page, lang="eng")
                    # print(text)
                    if searchq(text,q) == True:
                        plist.append(page)
                if len(plist) > 0:
                    # now make pdf from pages in plist
                    pdfinzipfname = pdffile[0].name.replace(".pdf","-filtered.pdf")
                    zipfname = file.filename.replace(".zip","-filtered.zip")
                    # temp = io.BytesIO()
                    temp = io.BytesIO()
                    buff = io.BytesIO()
                    plist[0].save(temp, "PDF",resolution=100.0, save_all=True, append_images=plist[1:])
                    temp.seek(0)
                    # print(sys.getsizeof(temp))
                    with zipfile.ZipFile(buff,mode="w",compression=zipfile.ZIP_DEFLATED) as zipw:
                        zipw.writestr(pdfinzipfname,temp.read())
                    headers =  {'Content-Disposition': f'attachment; filename="{zipfname}"'}
                    return Response(buff.getvalue(), headers=headers)
            else:
                response.status_code = 422
                return {"message":"pdf file not found"}
                
        except Exception as e:
            response.status_code = 500
            return {"message":f"{traceback.format_exc()}"}
            
    else:
        response.status_code = 403
        return {"message":"wrong file type"}



# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}