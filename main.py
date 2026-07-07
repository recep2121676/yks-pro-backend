from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="YKS PRO Cloud OS API", version="2.0.0")

# --- BELLEK ÜZERİNDE GEÇİCİ VERİTABANI (TEST İÇİN) ---
# Sunucu her kapandığında sıfırlanır, bulutta test etmek için en hızlı yöntemdir.
KULLANICILAR = {}
CALISMALAR = []

# --- MODEL TANIMLAMALARI (DATA SCHEMAS) ---
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

# --- 1. KİMLİK DOĞRULAMA SİSTEMİ (AUTH API) ---
@app.post("/api/auth/kayit-ol", status_code=201)
def kayit_ol(veri: KayitModel):
    if veri.email in KULLANICILAR:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı!")
    
    # Basitçe kullanıcıyı hafızaya ekliyoruz
    token = str(uuid.uuid4())
    KULLANICILAR[veri.email] = {
        "isim": veri.isim,
        "sifre": veri.sifre, # Üretim aşamasında şifreler hash'lenmelidir.
        "token": token
    }
    return {"message": "Kayıt başarılı", "token": token}

@app.post("/api/auth/giris-yap")
def giris_yap(veri: GirisModel):
    user = KULLANICILAR.get(veri.email)
    if not user or user["sifre"] != veri.sifre:
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı!")
    
    return {
        "access_token": user["token"],
        "kullanici_adi": user["isim"],
        "token_type": "bearer"
    }

# --- 2. AKADEMİK VERİ VE KOTA SİSTEMİ (CORE API) ---
@app.post("/api/akademi/calisma-ekle")
def calisma_ekle(token: str, veri: CalismaModel):
    # Token kontrolü
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
    
    # Kullanıcının bugünkü toplam verilerini hesapla
    toplam_soru = 0
    toplam_dk = 0
    
    for c in CALISMALAR:
        if c["email"] == kullanici_email and c["tarih"] == bugun:
            toplam_soru += c["soru"]
            toplam_dk += c["odak_suresi_dk"]

    # SaaS Mantığı: Günlük Kota Kontrolü (Örn: 250 Soru ve 240 Dk odaklanma)
    hedef_soru = 250
    hedef_dk = 240
    guilt_free_aktif = toplam_soru >= hedef_soru and toplam_dk >= hedef_dk

    return {
        "gunluk_soru": toplam_soru,
        "gunluk_dk": toplam_dk,
        "guilt_free": guilt_free_aktif
    }