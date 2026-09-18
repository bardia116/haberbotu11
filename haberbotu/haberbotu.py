import os
import requests
import xml.etree.ElementTree as ET
from google import genai
from pydantic import BaseModel, Field
from typing import List
import sqlite3


class haber(BaseModel):
    konu: str = Field(description="Haberlerin kategorize edildiği ana konu başlığı")
    baslik: str = Field(description="Google News'ten çekilen haberlerin başlığı")
    url: str = Field(description="Google News'ten alınan haberlerin linki")

class HaberListesi(BaseModel):
    haberler: List[haber] = Field(description="haber listesi")


print("Haberler çekiliyor...")
url_adresi = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
cevap = requests.get(url_adresi)
root = ET.fromstring(cevap.content)

toplanan_haberler = ""
for item in root.findall('.//item')[:10]: 
    title = item.find('title').text
    link = item.find('link').text
    toplanan_haberler += f"- Başlık: {title} | Link: {link}\n"


print("Yapay zeka analiz ediyor...")

client=genai.Client(api_key=os.environ["AQ.Ab8RN6JKUTQ24a5RfV-lJ0Kri8tFC8hRRjJAdY8weFWPOqozxw"])

prompt = f"""
Aşağıdaki haber başlıklarını analiz et. Her birini en uygun konuya (Teknoloji, Ekonomi, Spor, Savunma, Gündem vb.) göre kategorize et.

Haberler:
{toplanan_haberler}
"""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": HaberListesi.model_json_schema()
    }
)
sonuc = HaberListesi.model_validate_json(interaction.output_text)

print("Veritabanına kaydediliyor...")
baglanti = sqlite3.connect("gundem_haberleri.db")
imlec = baglanti.cursor()

imlec.execute("""
CREATE TABLE IF NOT EXISTS haberler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konu TEXT,
    baslik TEXT,
    url TEXT
)
""")

for tek_haber in sonuc.haberler:
    imlec.execute("INSERT INTO haberler (konu, baslik, url) VALUES (?, ?, ?)", (tek_haber.konu, tek_haber.baslik, tek_haber.url))
    print(f"✅ Eklendi: {tek_haber.konu} | {tek_haber.baslik}")

baglanti.commit()
baglanti.close()

print("\n🎉 İşlem tamamlandı! gundem_haberleri.db dosyası oluşturuldu/güncellendi.")