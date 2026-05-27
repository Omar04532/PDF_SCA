"""
أدوات مساعدة للبحث عن الكلمات المفتاحية
"""


def clean_keyword(keyword: str) -> str:
    """تنظيف الكلمة المفتاحية من علامات ترقيم زائدة"""
    return keyword.strip().lower().replace("  ", " ")


def categorize_keyword(keyword: str) -> str:
    """تصنيف الكلمة حسب النيتش"""
    children_terms = ["kid", "child", "children", "toddler", "baby", "preschool"]
    educational_terms = ["learn", "educational", "school", "abc", "123", "stem"]
    emotional_terms = ["feelings", "emotions", "anxiety", "confidence", "social"]
    bedtime_terms = ["bedtime", "sleep", "night", "dream", "nap"]

    kw_lower = keyword.lower()

    if any(t in kw_lower for t in emotional_terms):
        return "Social-Emotional 🔵"
    elif any(t in kw_lower for t in educational_terms):
        return "Educational 📚"
    elif any(t in kw_lower for t in bedtime_terms):
        return "Bedtime 🌙"
    elif any(t in kw_lower for t in children_terms):
        return "General Children 🧸"
    else:
        return "Other 📦"


def estimate_competition_score(keyword: str) -> str:
    """تقدير مستوى المنافسة بناءً على طول الكلمة والتعميم"""
    words = keyword.split()
    if len(words) >= 5:
        return "Low 🔵"
    elif len(words) >= 3:
        return "Medium 🟡"
    else:
        return "High 🔴"


def estimate_search_intent(keyword: str) -> str:
    """تقدير نية البحث"""
    kw_lower = keyword.lower()
    if any(w in kw_lower for w in ["buy", "purchase", "order", "best"]):
        return "Transactional 💰"
    elif any(w in kw_lower for w in ["how to", "what is", "guide", "tips"]):
        return "Informational ℹ️"
    elif any(w in kw_lower for w in ["for", "about", "ages", "toddler"]):
        return "Navigational 🧭"
    else:
        return "General 🔍"
