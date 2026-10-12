import hashlib, re, tempfile, uuid
from pathlib import Path
from .models import Chunk

def split_text(text,size=850,overlap=120):
    text=re.sub(r'\s+',' ',text).strip()
    if not text: return []
    out=[]; start=0
    while start<len(text):
        end=min(len(text),start+size)
        if end<len(text):
            boundary=max(text.rfind('. ',start,end),text.rfind(' ',start,end)); end=boundary+1 if boundary>start+150 else end
        out.append(text[start:end].strip())
        if end >= len(text): break
        start=max(end-overlap,start+1)
    return out

def make_chunks(name,content_type,parts):
    doc=hashlib.sha1(name.encode()).hexdigest()[:12]; chunks=[]
    for location,text,timing in parts:
        for piece in split_text(text):
            chunks.append(Chunk(id=str(uuid.uuid4()),document_id=doc,document_name=name,content_type=content_type,text=piece,page_number=location if content_type in ('pdf','docx') else None,slide_number=location if content_type=='pptx' else None,start_seconds=timing[0] if timing else None,end_seconds=timing[1] if timing else None))
    return chunks

def ingest_upload(upload):
    name=upload.name; ext=Path(name).suffix.lower(); data=upload.getvalue()
    if ext=='.pdf':
        import fitz
        doc=fitz.open(stream=data,filetype='pdf'); parts=[(i+1,p.get_text('text'),None) for i,p in enumerate(doc)]
        if not any(t.strip() for _,t,_ in parts): raise ValueError('No selectable text was found. This appears scanned; OCR is required before indexing.')
        return make_chunks(name,'pdf',parts)
    if ext=='.pptx':
        from pptx import Presentation
        with tempfile.NamedTemporaryFile(suffix='.pptx',delete=False) as f: f.write(data); path=f.name
        prs=Presentation(path); return make_chunks(name,'pptx',[(i+1,' '.join(s.text for s in slide.shapes if hasattr(s,'text')),None) for i,slide in enumerate(prs.slides)])
    if ext=='.docx':
        from docx import Document
        with tempfile.NamedTemporaryFile(suffix='.docx',delete=False) as f: f.write(data); path=f.name
        return make_chunks(name,'docx',[(1,' '.join(p.text for p in Document(path).paragraphs),None)])
    if ext in ('.txt','.vtt','.srt'):
        raw=data.decode('utf-8',errors='replace'); stamps=re.findall(r'(\d{1,2}):(\d{2})(?::(\d{2}))?',raw); sec=int(stamps[0][0])*60+int(stamps[0][1]) if stamps else None
        clean=re.sub(r'^\d+$|\d{2}:\d{2}(?::\d{2})?[,.]\d+\s*-->', '',raw,flags=re.M); return make_chunks(name,'transcript',[(None,clean,(sec,None) if sec is not None else None)])
    if ext in ('.mp4','.mov','.mkv','.webm'): raise ValueError('Video needs FFmpeg plus a configured transcription service. Upload its TXT/VTT transcript for the offline workflow.')
    raise ValueError('Unsupported file. Upload PDF, PPTX, DOCX, TXT, VTT, or SRT.')
