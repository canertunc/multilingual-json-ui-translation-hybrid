# Hibrit Yaklaşımla Çok Dilli JSON Arayüz Çevirisi

Bu proje, UI/Admin panel JSON dosyalarını yüksek kalitede çevirmek için gelişmiş hibrit bir sistem sunar. Helsinki-NLP'nin opus-mt modellerini kullanarak **Türkçe** → **İngilizce** → **Almanca** çeviri zinciri ile yüksek kaliteli çeviriler sağlar.

## Kurulum

### 1. Depoyu Klonlayın veya İndirin
```bash
git clone [repository-url]
cd multilingual-json-ui-translation-hybrid
```

### 2. Gerekli Paketleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. İlk Çalıştırma
```bash
python hybrid_translator.py
```

> **Not**: İlk çalıştırmada modeller otomatik olarak indirilecektir (~1-2 GB).

## Özellikler

### Hibrit Çeviri Sistemi
- **Terminoloji Sözlüğü**: UI/Admin panel spesifik terimlerin doğru çevirileri
- **Kalite Kontrol**: Çeviri sonrası otomatik skorlama ve hata tespiti
- **Post-Processing**: Yaygın hataları otomatik düzeltme
- **Çoklu Strateji**: Terminoloji + AI Model kombinasyonu
- **HTML Etiket Koruma**: HTML yapısını bozmadan çeviri

## Gereksinimler

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
python hybrid_translator.py
```

**Çıktılar:**
- `en_jsons_hybrid/` - İngilizce çeviriler
- `de_jsons_hybrid/` - Almanca çeviriler

## Klasör Yapısı

```
multilingual-json-ui-translation-hybrid/
├── hybrid_translator.py                # hibrit otomatik çeviri scripti
├── terminology_dict.json               # Özel terimler ve sabit çeviriler için kullanılan sözlük dosyası
├── requirements.txt                   
├── README.md                          
├── tr_jsons_hybrid/                    # Türkçe JSON dosyaları
│   ├── menu.json
│   ├── buttons.json
│   └── labels.json
├── en_jsons_hybrid/                    # İngilizce çeviriler (otomatik oluşur)
│   ├── menu.json
│   ├── buttons.json
│   └── labels.json
├── de_jsons_hybrid/                    # Almanca çeviriler (otomatik oluşur)
│   ├── menu.json
│   ├── buttons.json
│   └── labels.json
├── notebooks/                          # Geliştirme süreci ve test amaçlı Colab defterleri
│   ├── tr_to_eng.ipynb                 # Türkçe → İngilizce çeviri testleri
│   └── eng_to_de.ipynb                 # İngilizce → Almanca çeviri testleri
└── reports/                            # Karşılaştırmalı model değerlendirme raporları
    ├── Turkce_Ingilizce_Ceviri_Modelleri_Karsilastirma_Raporu.pdf
    └── Ingilizce_Almanca_Ceviri_Modelleri_Karsilastirma_Raporu.pdf
```

## Teknik Detaylar

### Kullanılan Modeller

- **Türkçe → İngilizce**: `Helsinki-NLP/opus-mt-tr-en`
- **İngilizce → Almanca**: `Helsinki-NLP/opus-mt-en-de`

### HTML Etiket Koruması

Sistem, JSON içindeki HTML etiketlerini korur:

```json
{
  "BUTTON_NEXT": "İleri <i class='fal fa-chevron-right ml-2'></i>",
  // Çeviri sonucu:
  "BUTTON_NEXT": "Next <i class='fal fa-chevron-right ml-2'></i>"
}
```

```json
{
  "ERROR_MESSAGE": "Hata: <strong>Geçersiz değer</strong> girildi",
  // Çeviri sonucu:
  "ERROR_MESSAGE": "Error: <strong>Invalid value</strong> entered"
}
```

## İyileştirmeler

### Tespit Edilen Problemler:
- "CURRENCIES": "Döviz Kurları" → "Mercenary Kurds" 
- "LOGIN": "Giriş" → "Introduction"
- "CONTRACTS": "Abonelikler" → "Absorptions"

### Hibrit Sistem Çözümleri:
- **Terminoloji Sözlüğü**: UI terimleri için doğru çeviriler
- **Kalite Kontrol**: Yanlış çevirileri otomatik tespit
- **Post-Processing**: Bilinen hataları düzeltme
- **HTML Koruma**: Etiketleri bozmadan çeviri

## Özelleştirme

### Terminoloji Sözlüğü Güncelleme

`terminology_dict.json` dosyasını düzenleyerek yeni terimler ekleyebilirsiniz:

```json
{
  "admin_ui_terms": {
    "turkish_to_english": {
      "yeni_terim": "new_term",
      "giriş": "login",
      "çıkış": "logout"
    },
    "english_to_german": {
      "new_term": "neuer_begriff",
      "login": "anmeldung",
      "logout": "abmeldung"
    }
  }
}
```

### Gelişmiş Kullanım

Kod içinde şu parametreleri değiştirebilirsiniz:
- `max_length`: Çeviri maksimum uzunluğu (varsayılan: 512)
- Model isimleri
- Çıktı dosya formatları

### Kalite Kriterleri

Kalite skorlama kriterleri:
- **90-100**: Mükemmel çeviri
- **70-89**: İyi çeviri  
- **50-69**: Orta kalite (inceleme önerilir)
- **0-49**: Düşük kalite (revizyon gerekli)

## Çeviri Süreci

1. `tr_jsons_hybrid/` klasöründeki Türkçe JSON dosyaları okunur
2. Türkçe → İngilizce çeviri yapılır (AI model + post-processing + terminoloji)
3. İngilizce → Almanca çeviri yapılır (AI model + post-processing + terminoloji)
4. Sonuçlar ilgili klasörlere kaydedilir

> **Not**: Her iki çeviri adımında da hibrit sistem devreye girer - AI model çevirisi, terminoloji düzeltmeleri ve post-processing hata giderme işlemleri uygulanır.
