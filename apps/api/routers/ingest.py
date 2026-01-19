from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/docs")
async def upload_doc(file: UploadFile = File(...)):
    # Day 3: store file + metadata, chunk, embed, index
    content = await file.read()
    return {"filename": file.filename, "bytes": len(content), "next": "Day 3: chunk + embed + store"}
