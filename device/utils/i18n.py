import json
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from ..config import config

class I18nManager:
    """Internationalization manager for loading and managing translations"""
    
    def __init__(self):
        self.current_lang = config.UI_LANG
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        i18n_dir = Path(__file__).parent.parent / "kiosk" / "assets" / "i18n"
        
        if not i18n_dir.exists():
            logger.warning(f"I18n directory not found: {i18n_dir}")
            return
        
        for lang_file in i18n_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load translations for {lang_code}: {e}")
    
    def set_language(self, lang_code: str):
        """Set current language"""
        if lang_code in self.translations:
            self.current_lang = lang_code
            logger.info(f"Language set to {lang_code}")
        else:
            logger.warning(f"Language {lang_code} not available")
    
    def get_text(self, key: str, fallback: Optional[str] = None) -> str:
        """Get translated text for key"""
        # Try current language first
        if self.current_lang in self.translations:
            text = self.translations[self.current_lang].get(key)
            if text:
                return text
        
        # Try fallback language (zh-CN)
        if "zh-CN" in self.translations and self.current_lang != "zh-CN":
            text = self.translations["zh-CN"].get(key)
            if text:
                return text
        
        # Return fallback or key itself
        return fallback or key
    
    def get_all_languages(self) -> Dict[str, str]:
        """Get all available languages with display names"""
        language_names = {
            "zh-CN": "简体中文",
            "en-US": "English"
        }
        
        available = {}
        for lang_code in self.translations:
            available[lang_code] = language_names.get(lang_code, lang_code)
        
        return available

# Global i18n manager instance
i18n = I18nManager()

# Convenience function for translations
def t(key: str, fallback: Optional[str] = None) -> str:
    """Get translated text (shorthand)"""
    return i18n.get_text(key, fallback)