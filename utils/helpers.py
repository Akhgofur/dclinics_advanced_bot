
from locales.en import EN
from locales.uz import UZ
from locales.ru import RU

def get_full_name(user, isShort = False, withoutSurname = False):
    def get_attr(obj, attr):
        if isinstance(obj, dict):
            return obj.get(attr, '')
        return getattr(obj, attr, '')
    
    if isShort:
        return f"{get_attr(user, 'last_name') or ''} {get_attr(user, 'first_name')[0] or ''}".strip()
    
    if withoutSurname:
        return f"{get_attr(user, 'last_name') or ''} {get_attr(user, 'first_name') or ''}".strip()    

    return f"{get_attr(user, 'last_name') or ''} {get_attr(user, 'first_name') or ''} {get_attr(user, 'surname') or ''}".strip()

def get_safe_attribute(obj, attr, default = "Неизвестно", number = False):
    val = obj
    for part in attr.split('.'):
        if val is not None and part in val:
            val = val.get(part)
        else:
            val = default
            break
        
        
    if number:
        return float(val or default)
    return val or default





JSON_DATA = {"uz": UZ, "ru": RU, 'en': EN}


def get_translation(lang, message):
    return JSON_DATA.get(lang, "ru").get(message) or ""
