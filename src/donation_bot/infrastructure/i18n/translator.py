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
        # -- start / main menu ------------------------------------------------
        "start.greeting.public": (
            "Assalomu alaykum! 🌙\n\n"
            "Bu — anonim xayriya boti.\n"
            "🔒 Sizning shaxsingiz hech qachon saqlanmaydi.\n"
            "🔍 Barcha xayriya va sarflar shaffof hisobotlarda ko'rinadi.\n\n"
            "Quyidagi tugmalardan foydalaning 👇"
        ),
        "start.greeting.staff": (
            "Assalomu alaykum, {name}! 👋\n"
            "Sizning rolingiz: {role}\n\n"
            "Quyidagi tugmalardan foydalaning 👇"
        ),
        "menu.title": "🏠 Asosiy menyu",
        "menu.hint": "Kerakli bo'limni tanlang 👇",
        # main-menu buttons
        "menu.donate": "💳 Xayriya qilish",
        "menu.statistics": "📊 Statistika",
        "menu.reports": "📈 Hisobotlar",
        "menu.record_donation": "➕ Xayriyani kiritish",
        "menu.record_expense": "➖ Sarfni kiritish",
        "menu.recent_entries": "📄 So'nggi yozuvlar",
        "menu.manage_staff": "👥 Xodimlar",
        "menu.configure_account": "💳 Hisob raqami",
        "menu.audit_log": "🗂 Audit jurnali",
        # -- common / navigation ---------------------------------------------
        "common.back": "🔙 Orqaga",
        "common.cancel": "❌ Bekor qilish",
        "common.confirm": "✅ Tasdiqlash",
        "common.skip": "⏭ O'tkazib yuborish",
        "common.cancelled": "❌ Amal bekor qilindi.\nAsosiy menyuga qaytdingiz.",
        "common.unknown": "Iltimos, quyidagi tugmalardan birini tanlang 👇",
        # -- donate / account -------------------------------------------------
        "donate.title": "💳 Xayriya qilish",
        "donate.instructions": "Quyidagi hisob raqamiga xayriya qilishingiz mumkin:",
        "donate.privacy": (
            "🔒 Sizning shaxsingiz saqlanmaydi.\n"
            "🔍 Har bir mablag' shaffof hisobotlarda aks etadi."
        ),
        "account.title": "🏦 Xayriya hisobi",
        "account.label": "📌 Nomi: {label}",
        "account.number": "💳 Raqam: {value}",
        "account.holder": "👤 Egasi: {holder}",
        "account.none": "ℹ️ Hozircha hisob raqami sozlanmagan.",
        "account.disabled": "⏸ Hozircha xayriyalar qabul qilinmayapti.",
        # -- reports ----------------------------------------------------------
        "reports.choose_period": "📈 Qaysi davr uchun hisobot kerak?",
        "reports.today": "📅 Bugun",
        "reports.month": "🗓 Bu oy",
        "reports.year": "📆 Bu yil",
        "reports.all_time": "♾ Butun davr",
        "report.title": "📈 Hisobot — {label}",
        "report.total_in": "🟢 Qabul qilingan:  {amount}",
        "report.total_out": "🔴 Sarflangan:      {amount}",
        "report.net": "💰 Qoldiq:           {amount}",
        "report.counts": "🧾 Xayriyalar: {donations} ta  •  Sarflar: {expenses} ta",
        "report.usage_header": "📋 Sarflar tafsiloti:",
        "report.usage_line": "  #{ref} — {amount} — {desc}",
        "report.no_expenses": "Bu davrda sarflar bo'lmagan.",
        # -- statistics -------------------------------------------------------
        "stats.title": "📊 Statistika (qoldiq)",
        "stats.today": "📅 Bugun:        {amount}",
        "stats.this_month": "🗓 Bu oy:        {amount}",
        "stats.this_year": "📆 Bu yil:       {amount}",
        "stats.all_time": "♾ Butun davr:   {amount}",
        # -- recent entries ---------------------------------------------------
        "recent.title": "📄 So'nggi yozuvlar:",
        "recent.empty": "Hozircha yozuvlar yo'q.",
        "recent.line_donation": "🟢 #{ref} • {amount} • {date}{reversed}",
        "recent.line_expense": "🔴 #{ref} • {amount} • {date} • {desc}{reversed}",
        "recent.reversed_mark": "  ↩️ tuzatilgan",
        # -- donation flow ----------------------------------------------------
        "donation.ask_amount": "➕ Xayriya summasini kiriting (so'mda):\n\nMasalan: 50000",
        "donation.ask_source": "📥 Xayriya manbasini tanlang:",
        "donation.source_cash": "💵 Naqd",
        "donation.source_bank": "🏦 Bank o'tkazmasi",
        "donation.ask_note": (
            "📝 Maxfiy izoh (ixtiyoriy — faqat xodimlar ko'radi).\n"
            "⚠️ Xayriya qiluvchining ismini YOZMANG.\n\n"
            "Izohsiz davom etish uchun «⏭ O'tkazib yuborish»."
        ),
        "donation.note_none": "yo'q",
        "donation.confirm_title": "Quyidagini tasdiqlaysizmi? ⤵️",
        "donation.summary": "➕ Xayriya\n💰 Summa: {amount}\n📥 Manba: {source}\n📝 Izoh: {note}",
        "donation.recorded": "✅ Xayriya qabul qilindi!\n🔖 Havola: #{ref}",
        # -- expense flow -----------------------------------------------------
        "expense.ask_amount": "➖ Sarf summasini kiriting (so'mda):\n\nMasalan: 30000",
        "expense.ask_category": "🏷 Sarf turkumini tanlang:",
        "expense.ask_description": (
            "📝 Sarf tavsifini kiriting.\n"
            "ℹ️ Bu ma'lumot OMMAVIY — mablag' nimaga ishlatilganini yozing:"
        ),
        "expense.confirm_title": "Quyidagini tasdiqlaysizmi? ⤵️",
        "expense.summary": "➖ Sarf\n💰 Summa: {amount}\n🏷 Turkum: {category}\n📝 Tavsif: {desc}",
        "expense.recorded": "✅ Sarf qayd etildi!\n🔖 Havola: #{ref}",
        "expense.overspent_warning": "⚠️ Diqqat: qoldiq manfiy bo'lib qoldi.",
        # -- staff management -------------------------------------------------
        "staff.ask_telegram_id": "👥 Yangi xodimning Telegram ID raqamini kiriting:",
        "staff.ask_role": "🎭 Rolni tanlang:",
        "staff.role_treasurer": "🧾 G'aznachi",
        "staff.role_admin": "🛡 Bosh admin",
        "staff.invalid_id": "❌ Telegram ID faqat raqamlardan iborat bo'lishi kerak.\nQaytadan kiriting:",
        "staff.registered": "✅ Xodim muvaffaqiyatli qo'shildi.",
        "staff.already_registered": "⚠️ Bu Telegram ID allaqachon ro'yxatdan o'tgan.",
        # -- configure account ------------------------------------------------
        "account.ask_label": "🏦 Hisob nomini kiriting:\n\nMasalan: Asosiy karta",
        "account.ask_type": "💳 Hisob turini tanlang:",
        "account.type_card": "💳 Karta",
        "account.type_bank": "🏦 Bank hisob",
        "account.type_wallet": "👛 Hamyon",
        "account.ask_value": "🔢 Hisob raqamini kiriting:",
        "account.ask_holder": "👤 Hisob egasining ismini kiriting.\n\n«⏭ O'tkazib yuborish» — ixtiyoriy.",
        "account.updated": "✅ Xayriya hisobi yangilandi.",
        # -- audit ------------------------------------------------------------
        "audit.title": "🗂 So'nggi audit yozuvlari:",
        "audit.empty": "Audit yozuvlari yo'q.",
        "audit.line": "• {time} — {action}{ref}",
        "audit.action.donation.recorded": "Xayriya kiritildi",
        "audit.action.expense.recorded": "Sarf kiritildi",
        "audit.action.entry.reversed": "Tuzatish kiritildi",
        "audit.action.annotation.added": "Izoh qo'shildi",
        "audit.action.annotation.redacted": "Izoh tozalandi",
        "audit.action.staff.registered": "Xodim qo'shildi",
        "audit.action.staff.seeded": "Boshlang'ich admin",
        "audit.action.account.configured": "Hisob o'zgartirildi",
        # -- money & errors ---------------------------------------------------
        "money.suffix": "so'm",
        "error.permission_denied": "⛔️ Sizda bu amal uchun ruxsat yo'q.",
        "error.invalid_amount": "❌ Noto'g'ri summa.\nMusbat butun son kiriting (masalan: 50000):",
        "error.empty_text": "❌ Bo'sh bo'lishi mumkin emas. Iltimos, matn kiriting:",
        "error.generic": "⚠️ Kutilmagan xatolik yuz berdi. Keyinroq urinib ko'ring.",
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
