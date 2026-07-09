"""Minimal, dependency-free translation layer.

v1 ships Uzbek (``uz``). Adding Russian/English later means adding a catalog, not
editing handlers. Missing keys render as ``<key>`` so gaps are obvious in testing.
All user-facing strings go through :class:`Translator`.
"""

from __future__ import annotations

DEFAULT_LOCALE = "uz"

# locale -> key -> template
CATALOG: dict[str, dict[str, str]] = {
    "uz": {
        # start / menu
        "start.greeting.public": (
            "Assalomu alaykum! Bu anonim xayriya boti.\n"
            "Bu yerda xayriyalar va sarflar shaffof tarzda ko'rsatiladi. "
            "Sizning shaxsingiz hech qachon saqlanmaydi."
        ),
        "start.greeting.staff": "Xush kelibsiz, {name}! Sizning rolingiz: {role}.",
        "menu.title": "Asosiy menyu:",
        "menu.donate": "💳 Xayriya qilish",
        "menu.statistics": "📈 Statistika",
        "menu.reports": "📊 Hisobotlar",
        "menu.about": "ℹ️ Bot haqida",
        "menu.record_donation": "➕ Xayriyani kiritish",
        "menu.record_expense": "➖ Sarfni kiritish",
        "menu.recent_entries": "🧾 So'nggi yozuvlar",
        "menu.manage_staff": "👥 Xodimlarni boshqarish",
        "menu.configure_account": "💳 Hisob raqamini sozlash",
        "menu.audit_log": "🗂 Audit jurnali",
        # reports
        "reports.choose_period": "Davrni tanlang:",
        "reports.today": "Bugun",
        "reports.month": "Bu oy",
        "reports.year": "Bu yil",
        "reports.all_time": "Butun davr",
        "report.title": "📊 Hisobot — {label}",
        "report.total_in": "Jami qabul qilingan: {amount}",
        "report.total_out": "Jami sarflangan: {amount}",
        "report.net": "Qoldiq: {amount}",
        "report.counts": "Xayriyalar: {donations} ta, sarflar: {expenses} ta",
        "report.usage_header": "Sarflar (mablag' nimaga ishlatilgani):",
        "report.usage_line": "#{ref} — {amount}: {desc}",
        "report.no_expenses": "Bu davrda sarflar bo'lmagan.",
        # statistics
        "stats.title": "📈 Statistika:",
        "stats.today": "Bugun — qoldiq: {amount}",
        "stats.this_month": "Bu oy — qoldiq: {amount}",
        "stats.this_year": "Bu yil — qoldiq: {amount}",
        "stats.all_time": "Butun davr — qoldiq: {amount}",
        # donation account
        "account.title": "💳 Xayriya uchun hisob:",
        "account.label": "Nomi: {label}",
        "account.number": "Raqam: {value}",
        "account.holder": "Egasi: {holder}",
        "account.none": "Hozircha hisob raqami sozlanmagan.",
        "account.disabled": "Hozircha xayriyalar qabul qilinmayapti.",
        # money
        "money.suffix": "so'm",
        # common
        "common.back": "⬅️ Orqaga",
        "common.cancel": "Bekor qilish",
        "common.confirm": "✅ Tasdiqlash",
        "common.skip": "O'tkazib yuborish",
        "common.now": "Hozir",
        "common.done": "✅ Bajarildi",
        # donation flow
        "donation.ask_amount": "Xayriya summasini kiriting (so'mda):",
        "donation.ask_source": "Manbani tanlang:",
        "donation.source_cash": "Naqd",
        "donation.source_bank": "Bank o'tkazmasi",
        "donation.ask_note": "Ixtiyoriy maxfiy izoh (xodimlar uchun; ISM YOZMANG). Yoki o'tkazib yuboring:",
        "donation.recorded": "✅ Xayriya kiritildi. Havola: #{ref}",
        # expense flow
        "expense.ask_amount": "Sarf summasini kiriting (so'mda):",
        "expense.ask_category": "Turkumni tanlang:",
        "expense.ask_description": "Sarf tavsifi (ommaviy — mablag' nimaga ishlatildi):",
        "expense.recorded": "✅ Sarf kiritildi. Havola: #{ref}",
        "expense.overspent_warning": "⚠️ Diqqat: qoldiq manfiy bo'lib qoldi.",
        # staff management
        "staff.ask_telegram_id": "Yangi xodimning Telegram ID raqamini kiriting:",
        "staff.ask_role": "Rolni tanlang:",
        "staff.role_treasurer": "G'aznachi",
        "staff.role_admin": "Bosh admin",
        "staff.registered": "✅ Xodim qo'shildi.",
        "staff.already_registered": "Bu Telegram ID allaqachon ro'yxatdan o'tgan.",
        # errors
        "error.permission_denied": "Sizda bu amal uchun ruxsat yo'q.",
        "error.not_found": "Topilmadi.",
        "error.invalid_amount": "Noto'g'ri summa. Musbat butun son kiriting.",
        "error.generic": "Kutilmagan xatolik yuz berdi. Keyinroq urinib ko'ring.",
    }
}


class Translator:
    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        self._locale = locale if locale in CATALOG else DEFAULT_LOCALE
        self._catalog = CATALOG[self._locale]

    @property
    def locale(self) -> str:
        return self._locale

    def t(self, key: str, /, **kwargs: object) -> str:
        template = self._catalog.get(key)
        if template is None:
            return f"<{key}>"
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template


def get_translator(locale: str = DEFAULT_LOCALE) -> Translator:
    return Translator(locale)
