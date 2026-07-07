from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uvicorn
import uuid

app = FastAPI(title="YKS PRO Cloud API")

KULLANICILAR = {}
CALISMALAR = []

class KayitModel(BaseModel):
    isim: str
    email: EmailStr
    sifre: str

class GirisModel(BaseModel):
    email: EmailStr
    sifre: str

class CalismaModel(BaseModel):
    ders: str
    soru: int
    odak_suresi_dk: int

@app.get("/")
def home():
    return {"status": "ok", "message": "YKS PRO Server is running!"}

@app.post("/api/auth/kayit-ol")
def kayit_ol(veri: KayitModel):
    if veri.email in KULLANICILAR:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı!")
    token = str(uuid.uuid4())
    KULLANICILAR[veri.email] = {"isim": veri.isim, "sifre": veri.sifre, "token": token}
    return {"message": "Kayıt başarılı", "token": token}

@app.post("/api/auth/giris-yap")
def giris_yap(veri: GirisModel):
    user = KULLANICILAR.get(veri.email)
    if not user or user["sifre"] != veri.sifre:
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı!")
    return {"access_token": user["token"], "kullanici_adi": user["isim"], "token_type": "bearer"}

@app.post("/api/akademi/calisma-ekle")
def calisma_ekle(token: str, veri: CalismaModel):
    kullanici_email = None
    for email, u_data in KULLANICILAR.items():
        if u_data["token"] == token:
            kullanici_email = email
            break
    if not kullanici_email:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı oturumu!")

    yeni_kayit = {
        "email": kullanici_email,
        "ders": veri.ders,
        "soru": veri.soru,
        "odak_suresi_dk": veri.odak_suresi_dk,
        "tarih": datetime.now().strftime("%Y-%m-%d")
    }
    CALISMALAR.append(yeni_kayit)
    return {"status": "success", "message": "Çalışma buluta başarıyla işlendi."}

@app.get("/api/akademi/panel-verileri")
def panel_verileri(token: str):
    kullanici_email = None
    for email, u_data in KULLANICILAR.items():
        if u_data["token"] == token:
            kullanici_email = email
            break
    if not kullanici_email:
        raise HTTPException(status_code=401, detail="Geçersiz oturum!")

    bugun = datetime.now().strftime("%Y-%m-%d")
    toplam_soru = 0
    toplam_dk = 0
    
    for c in CALISMALAR:
        if c["email"] == kullanici_email and c["tarih"] == bugun:
            toplam_soru += c["soru"]
            toplam_dk += c["odak_suresi_dk"]

    return {
        "gunluk_soru": toplam_soru,
        "gunluk_dk": toplam_dk,
        "guilt_free": toplam_soru >= 250 and toplam_dk >= 240
    }
