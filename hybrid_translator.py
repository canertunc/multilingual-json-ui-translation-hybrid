"""
Hibrit JSON Çeviri Sistemi
==========================

Bu sistem aşağıdaki özellikler ile gelişmiş çeviri sağlar:
1. Terminoloji sözlüğü ile domain-specific çeviriler
2. Kalite kontrol ve skorlama sistemi
3. Post-processing ile hata düzeltme
4. Çoklu model desteği
"""

import json
import re
import torch
import os
import glob
import difflib
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, List, Tuple, Any, Optional

class QualityChecker:
    """Çeviri kalitesi kontrol sistemi"""
    
    def __init__(self, terminology_file: str = "terminology_dict.json"):
        self.terminology = self.load_terminology(terminology_file)
        self.quality_patterns = self.terminology.get("quality_patterns", {})
        
    def load_terminology(self, file_path: str) -> dict:
        """Terminoloji sözlüğünü yükle"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Terminoloji dosyası bulunamadı: {file_path}")
            return {}
    
    def check_common_mistakes(self, text: str, target_lang: str) -> List[Dict]:
        """Yaygın hataları kontrol et"""
        mistakes = []
        common_mistakes = self.quality_patterns.get("common_mistakes", {}).get(target_lang, {})
        
        text_lower = text.lower()
        for correct_term, wrong_variants in common_mistakes.items():
            for wrong_term in wrong_variants:
                if wrong_term.lower() in text_lower:
                    mistakes.append({
                        "type": "common_mistake",
                        "wrong_term": wrong_term,
                        "correct_term": correct_term,
                        "confidence": 0.9
                    })
        
        return mistakes
    
    def calculate_quality_score(self, original: str, translated: str, target_lang: str) -> Dict:
        """Çeviri kalite skoru hesapla"""
        score = 100.0
        issues = []
        
        # Yaygın hataları kontrol et
        mistakes = self.check_common_mistakes(translated, target_lang)
        for mistake in mistakes:
            score -= 20  # Her yaygın hata için 20 puan düş
            issues.append(mistake)
        
        # Boş çeviri kontrolü
        if not translated.strip():
            score = 0
            issues.append({"type": "empty_translation", "confidence": 1.0})
        
        # Çok kısa çeviri kontrolü (orijinalin %20'sinden kısa)
        if len(translated) < len(original) * 0.2:
            score -= 15
            issues.append({"type": "too_short", "confidence": 0.7})
        
        # HTML etiket tutarlılığı
        orig_tags = set(re.findall(r'<[^>]+>', original))
        trans_tags = set(re.findall(r'<[^>]+>', translated))
        if orig_tags != trans_tags:
            score -= 10
            issues.append({"type": "html_mismatch", "confidence": 0.8})
        
        return {
            "score": max(0, score),
            "issues": issues,
            "needs_review": score < 70
        }

class TerminologyTranslator:
    """Terminoloji sözlüğü tabanlı çeviri sistemi"""
    
    def __init__(self, terminology_file: str = "terminology_dict.json"):
        self.terminology = self.load_terminology(terminology_file)
        
    def load_terminology(self, file_path: str) -> dict:
        """Terminoloji sözlüğünü yükle"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Terminoloji dosyası bulunamadı: {file_path}")
            return {}
    
    def get_term_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Terminoloji sözlüğünden çeviri bul"""
        terms = self.terminology.get("admin_ui_terms", {})
        
        if source_lang == "turkish" and target_lang == "english":
            return terms.get("turkish_to_english", {}).get(text.lower())
        elif source_lang == "english" and target_lang == "german":
            return terms.get("english_to_german", {}).get(text.lower())
        
        return None
    
    def translate_with_terminology(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, bool]:
        """Terminoloji sözlüğü ile çeviri yap"""
        # Önce exact match dene
        term_translation = self.get_term_translation(text, source_lang, target_lang)
        if term_translation:
            return term_translation, True
        
        # Partial match dene (kelime kelime)
        words = text.split()
        if len(words) > 1:
            translated_words = []
            has_terminology = False
            
            for word in words:
                clean_word = re.sub(r'[^\w\s]', '', word).lower()
                term_trans = self.get_term_translation(clean_word, source_lang, target_lang)
                if term_trans:
                    translated_words.append(term_trans)
                    has_terminology = True
                else:
                    translated_words.append(word)
            
            if has_terminology:
                return ' '.join(translated_words), True
        
        return text, False

class PostProcessor:
    """Post-processing ile çeviri düzeltme sistemi"""
    
    def __init__(self, terminology_file: str = "terminology_dict.json"):
        self.terminology_translator = TerminologyTranslator(terminology_file)
        self.quality_checker = QualityChecker(terminology_file)
    
    def fix_common_mistakes(self, text: str, target_lang: str) -> str:
        """Yaygın hataları düzelt"""
        mistakes = self.quality_checker.check_common_mistakes(text, target_lang)
        
        for mistake in mistakes:
            wrong_term = mistake["wrong_term"]
            correct_term = mistake["correct_term"]
            
            # Case-insensitive replace
            text = re.sub(re.escape(wrong_term), correct_term, text, flags=re.IGNORECASE)
        
        return text
    
    def apply_terminology_fixes(self, text: str, source_lang: str, target_lang: str) -> str:
        """Terminoloji sözlüğüne göre düzeltmeler yap"""
        # Terminoloji sözlüğünden ters çeviri tablosu oluştur
        reverse_terminology = {}
        terms = self.terminology_translator.terminology.get("admin_ui_terms", {})
        
        if source_lang == "turkish" and target_lang == "english":
            # Türkçe'den İngilizce'ye çeviri için doğru terimleri al
            for tr_term, en_term in terms.get("turkish_to_english", {}).items():
                reverse_terminology[tr_term.lower()] = en_term.lower()
        elif source_lang == "english" and target_lang == "german":
            # İngilizce'den Almanca'ya çeviri için doğru terimleri al  
            for en_term, de_term in terms.get("english_to_german", {}).items():
                reverse_terminology[en_term.lower()] = de_term.lower()
        
        # Yaygın yanlış çevirileri düzelt
        common_fixes = {
            "introduction": "login",  # Giriş → Introduction yerine Login
            "exit": "logout",         # Çıkış → Exit yerine Logout  
            "mercenary kurds": "exchange rates",  # Döviz → Mercenary Kurds yerine Exchange Rates
            "bayiers": "dealers",     # Bayiler → Bayiers yerine Dealers
            "varient": "variant",     # Varyant → Varient yerine Variant
            "copyed": "copied",       # Kopyalandı → Copyed yerine Copied
            "absorptions": "subscriptions", # Abonelik → Absorptions yerine Subscriptions
            "resorptionen": "abonnements"   # Almanca düzeltme
        }
        
        # Yaygın hataları düzelt
        text_lower = text.lower()
        for wrong, correct in common_fixes.items():
            if wrong in text_lower:
                # Kelime sınırlarını koruyarak değiştir
                pattern = r'\b' + re.escape(wrong) + r'\b'
                text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_capitalization(self, text: str) -> str:
        """Büyük/küçük harf düzenle"""
        # Cümle başlarını büyük harfle başlat
        text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        return text
    
    def process_translation(self, original: str, translated: str, source_lang: str, target_lang: str) -> Dict:
        """Çeviriyi post-process et"""
        processed = translated
        
        # 1. Yaygın hataları düzelt
        processed = self.fix_common_mistakes(processed, target_lang)
        
        # 2. Terminoloji düzeltmeleri yap
        processed = self.apply_terminology_fixes(processed, source_lang, target_lang)
        
        # 3. Büyük/küçük harf düzenle
        processed = self.normalize_capitalization(processed)
        
        # Kalite skoru hesapla
        quality = self.quality_checker.calculate_quality_score(original, processed, target_lang)
        
        return {
            "original": original,
            "raw_translation": translated,
            "processed_translation": processed,
            "quality": quality,
            "improved": processed != translated
        }

class HybridTranslator:
    """Hibrit çeviri sistemi - Terminoloji + Model + Post-processing"""
    
    def __init__(self):
        print("Hibrit Çeviri Sistemi Başlatılıyor...")
        
        # Cihaz ayarı
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Kullanılan cihaz: {self.device}")
        
        # Alt sistemleri başlat
        self.terminology_translator = TerminologyTranslator()
        self.post_processor = PostProcessor()
        self.quality_checker = QualityChecker()
        
        # Modelleri yükle
        self.load_models()
    
    def load_models(self):
        """Çeviri modellerini yükle"""
        print("AI Modelleri yükleniyor...")
        
        # Türkçe -> İngilizce modeli
        print("  Türkçe->İngilizce modeli yükleniyor...")
        self.tr_en_model_name = "Helsinki-NLP/opus-mt-tr-en"
        self.tr_en_tokenizer = AutoTokenizer.from_pretrained(self.tr_en_model_name)
        self.tr_en_model = AutoModelForSeq2SeqLM.from_pretrained(self.tr_en_model_name).to(self.device)
        
        # İngilizce -> Almanca modeli
        print("  İngilizce->Almanca modeli yükleniyor...")
        self.en_de_model_name = "Helsinki-NLP/opus-mt-en-de"
        self.en_de_tokenizer = AutoTokenizer.from_pretrained(self.en_de_model_name)
        self.en_de_model = AutoModelForSeq2SeqLM.from_pretrained(self.en_de_model_name).to(self.device)
        
        print("Tüm sistemler hazır!")
    
    def translate_text_hybrid(self, text: str, source_lang: str, target_lang: str, tokenizer, model) -> Dict:
        """Hibrit çeviri - Model + Terminoloji Post-processing"""
        
        # HTML etiketlerini koru
        if '<' in text:
            model_translation = self.translate_text_with_html(text, tokenizer, model)
        else:
            inputs = tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
            outputs = model.generate(**inputs, max_length=512)
            model_translation = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Post-processing ile terminoloji düzeltmeleri yap
        result = self.post_processor.process_translation(text, model_translation, source_lang, target_lang)
        result["method"] = "model+terminology_postprocess"
        
        return result
    
    def translate_text_with_html(self, text, tokenizer, model):
        """HTML etiketlerini koruyarak metni çevir"""
        if '<' not in text:
            inputs = tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
            outputs = model.generate(**inputs, max_length=512)
            return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        # HTML etiketleri ve metinleri ayır
        parts = re.split(r'(<[^>]*>)', text)
        translated_parts = []

        for part in parts:
            if not part:
                continue
            elif part.startswith('<') and part.endswith('>'):
                translated_parts.append(part)
            else:
                clean_text = part.strip()
                if clean_text:
                    inputs = tokenizer(clean_text, return_tensors="pt", truncation=True).to(self.device)
                    outputs = model.generate(**inputs, max_length=512)
                    translated = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

                    if part.startswith(' '):
                        translated = ' ' + translated
                    if part.endswith(' '):
                        translated = translated + ' '

                    translated_parts.append(translated)
                else:
                    translated_parts.append(part)

        return ''.join(translated_parts)
    
    def translate_json_hybrid(self, data, source_lang: str, target_lang: str, tokenizer, model):
        """JSON'u hibrit sistem ile çevir"""
        if isinstance(data, dict):
            return {k: self.translate_json_hybrid(v, source_lang, target_lang, tokenizer, model) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.translate_json_hybrid(i, source_lang, target_lang, tokenizer, model) for i in data]
        elif isinstance(data, str):
            result = self.translate_text_hybrid(data, source_lang, target_lang, tokenizer, model)
            return result["processed_translation"]
        else:
            return data
    
    def translate_file_hybrid(self, input_file: str, base_directory: str = "."):
        """Dosyayı hibrit sistem ile çevir"""
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Çıktı klasörlerini oluştur
        en_folder = os.path.join(base_directory, "en_jsons_hybrid")
        de_folder = os.path.join(base_directory, "de_jsons_hybrid")
        
        os.makedirs(en_folder, exist_ok=True)
        os.makedirs(de_folder, exist_ok=True)
        
        print(f"\n{input_file} işleniyor...")
        
        # JSON dosyasını oku
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                original_data = json.load(f)
        except Exception as e:
            print(f"Dosya okuma hatası: {e}")
            return
        
        # 1. Türkçe -> İngilizce çeviri
        print("  Türkçe -> İngilizce çeviri...")
        
        english_data = self.translate_json_hybrid(
            original_data, "turkish", "english", 
            self.tr_en_tokenizer, self.tr_en_model
        )
        
        # İngilizce çeviriyi kaydet
        english_file = os.path.join(en_folder, f"{base_name}.json")
        with open(english_file, "w", encoding="utf-8") as f:
            json.dump(english_data, f, ensure_ascii=False, indent=2)
        
        print(f"  İngilizce çeviri tamamlandı")
        
        # 2. İngilizce -> Almanca çeviri
        print("  İngilizce -> Almanca çeviri...")
        
        german_data = self.translate_json_hybrid(
            english_data, "english", "german",
            self.en_de_tokenizer, self.en_de_model
        )
        
        # Almanca çeviriyi kaydet
        german_file = os.path.join(de_folder, f"{base_name}.json")
        with open(german_file, "w", encoding="utf-8") as f:
            json.dump(german_data, f, ensure_ascii=False, indent=2)
        
        print(f"  Almanca çeviri tamamlandı")
    
    def run_hybrid(self, base_directory: str = "."):
        """Hibrit çeviri sistemini çalıştır"""
        print(f"\n{base_directory}/tr_jsons_hybrid klasöründe JSON dosyaları aranıyor...")
        
        tr_folder = os.path.join(base_directory, "tr_jsons_hybrid")
        if not os.path.exists(tr_folder):
            print("tr_jsons_hybrid klasörü bulunamadı!")
            return
        
        tr_files = glob.glob(os.path.join(tr_folder, "*.json"))
        
        if not tr_files:
            print("tr_jsons_hybrid klasöründe JSON dosyası bulunamadı!")
            return
        
        print(f"Bulunan dosyalar: {len(tr_files)}")
        
        # Her dosyayı çevir
        for file in tr_files:
            self.translate_file_hybrid(file, base_directory)
        
        print(f"\nÇeviri işlemi tamamlandı!")
        print(f"Çıktı klasörleri:")
        print(f"  en_jsons_hybrid/ - İngilizce çeviriler")
        print(f"  de_jsons_hybrid/ - Almanca çeviriler")

def main():
    """Ana fonksiyon"""
    try:
        translator = HybridTranslator()
        translator.run_hybrid()
    except KeyboardInterrupt:
        print("\n\nİşlem kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"\nHata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 