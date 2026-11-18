# Assistent AI — kompyuter ekranini boshqaruvchi yordamchi

Bu dastur Claude'ning **computer use** imkoniyati yordamida kompyuteringiz ekranini ko'radi va sichqoncha hamda klaviaturani o'zi boshqarib, siz bergan ishni bajaradi. Masalan, Chrome'da ochiq Google Sheets jadvalidagi `#REF!` xatolarini topib tuzatishi mumkin.

Claude Pro tarifi **kerak emas**. Dastur to'g'ridan-to'g'ri Anthropic API bilan ishlaydi, faqat API kalit kerak bo'ladi.

## Ikki xil ishlash usuli

1. **Chat.** Vazifani oddiy so'z bilan yozasiz, masalan "Chrome'ni och va ob-havoni ko'rsat". Claude ekranni boshqarib bajaradi, kerak bo'lsa sizdan savol so'raydi, siz javob yozib suhbatni davom ettirasiz. Chatga fayl ham biriktirish mumkin.
2. **Tezkor vazifalar.** Doimiy qilinadigan ishlar uchun bir marta **head prompt** (batafsil ko'rsatma) yozib, kerakli fayllarni biriktirib saqlab qo'yasiz. Keyin ro'yxatdan tanlab **▶ Ishga tushirish** tugmasini bosasiz (yoki ikki marta bosasiz). Natija Chat oynasida ko'rinadi va xohlasangiz o'sha yerda davom ettirasiz.

Dasturda namuna sifatida **"Google Sheets: #REF! xatolarini tuzatish"** vazifasi tayyor turadi.

## Nima kerak

- Windows 10 yoki 11 (macOS va Linux'da ham ishlashi kerak, lekin asosan Windows uchun sozlangan)
- [Python 3.10 yoki undan yangi](https://www.python.org/downloads/). O'rnatayotganda **"Add python.exe to PATH"** belgisini albatta qo'ying.
- Anthropic API kalit

### API kalitni olish

1. [console.anthropic.com](https://console.anthropic.com) saytida ro'yxatdan o'ting.
2. **Billing** bo'limida balansni to'ldiring (masalan $5). API ishlatilgan miqdorga qarab pullik.
3. **API Keys** → **Create Key** tugmasini bosing va `sk-ant-...` bilan boshlanadigan kalitni nusxalab oling. Kalitni hech kimga bermang.

## O'rnatish (Windows)

1. Ushbu repozitoriyani yuklab oling: GitHub sahifasida **Code → Download ZIP**, keyin arxivni biror papkaga oching. Yoki `git clone https://github.com/zane29-coder/assistent_ai`.
2. Papkadagi **`install.bat`** faylini ikki marta bosing. U kerakli kutubxonalarni o'rnatadi (1–3 daqiqa).
3. **`run.bat`** faylini ikki marta bosing. Dastur oynasi ochiladi.
4. **Sozlamalar** bo'limida API kalitni kiriting, **Saqlash**, keyin **API kalitni tekshirish** tugmasini bosing. "Kalit ishlayapti" degan xabar chiqishi kerak.

Qo'lda o'rnatmoqchi bo'lsangiz:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

API kalitni `ANTHROPIC_API_KEY` muhit o'zgaruvchisi orqali ham berish mumkin. Kalit faqat sizning kompyuteringizdagi `config.json` fayliga saqlanadi va GitHub'ga yuklanmaydi (`.gitignore`da).

## Birinchi sinov

1. Chrome'ni oching.
2. Dasturning **Chat** bo'limiga yozing: `Chrome'da yangi tab ochib, google.com ga kir va "Toshkent ob-havosi" deb qidir`.
3. **Yuborish** (yoki Ctrl+Enter) bosing.

Vazifa ishlayotganda asosiy oyna yashiriladi (ekranni to'smasligi uchun), o'ng yuqori burchakda kichik oyna qoladi. Unda Claude hozir nima qilayotgani va **■ To'xtatish** tugmasi bo'ladi. Ish tugagach asosiy oyna qaytadi va barcha qadamlar Chat'da ko'rinadi.

### #REF! xatolarini tuzatish

1. Chrome'da Google Sheets jadvalingizni oching va oynani ochiq qoldiring.
2. **Tezkor vazifalar** → **"Google Sheets: #REF! xatolarini tuzatish"** → **▶ Ishga tushirish**.
3. Kerak bo'lsa, **qo'shimcha izoh** maydoniga masalan `faqat "Hisobot" varag'ini tekshir` deb yozing.

Maslahat: agar jadvalning eski to'g'ri nusxasi yoki ustunlar tavsifi bo'lsa, uni `.xlsx`, `.csv` yoki skrinshot ko'rinishida vazifaga biriktiring. Claude to'g'ri havolani aniqlashda undan foydalanadi.

### O'z tezkor vazifangizni qo'shish

**+ Yangi vazifa** → nom va head prompt yozing → kerak bo'lsa fayl qo'shing → **Saqlash**. Head promptni qanchalik aniq yozsangiz, natija shunchalik yaxshi bo'ladi: qaysi dastur yoki sayt, qaysi tartibda ishlash kerak, nimalarga tegmaslik kerak va oxirida qanday hisobot berish kerakligini yozing. Vazifalar `tasks.json` faylida saqlanadi.

Biriktirish mumkin bo'lgan fayllar: rasmlar (png, jpg, webp, gif), PDF, Excel (`.xlsx`, formulalari bilan), matnli fayllar (txt, csv, json, md va boshqalar). Boshqa turdagi fayllarning faqat nomi va joylashuvi yuboriladi.

## Narxi haqida

Har bir qadamda ekran rasmi Claude'ga yuboriladi, shuning uchun to'lov qadamlar soniga bog'liq. Taxminan: oddiy vazifa (10–20 qadam) bir necha sentdan 30–50 sentgacha, uzun vazifa $1 va undan ko'p turishi mumkin. Pastki o'ng burchakda joriy suhbatga taxminiy sarf ko'rinib turadi.

Arzonlashtirish uchun **Sozlamalar**da:

- **Model**: `claude-sonnet-5-5` arzonroq, `claude-opus-5-5` (standart) aqlliroq.
- **Fikrlash darajasi (effort)**: `low` yoki `medium` arzonroq.
- **Skrinshot o'lchami**: 1024–1280 kichikroq va arzonroq, lekin mayda yozuvlar xiraroq ko'rinadi.
- **Eng ko'p qadam**: vazifa haddan tashqari cho'zilib ketmasligi uchun chegara.

Console'da **Billing → Limits** bo'limida oylik sarf chegarasini qo'yib qo'yish ham tavsiya etiladi.

## Xavfsizlik

- Dastur sizning **haqiqiy** kompyuteringizni boshqaradi. Ishlayotganda sichqoncha va klaviaturaga tegmang.
- **Favqulodda to'xtatish**: sichqonchani ekranning **chap-yuqori burchagiga** olib boring, yoki kichik oynadagi **■ To'xtatish** tugmasini bosing.
- Claude'ga parol, karta raqami kiritmaslik, xarid qilmaslik va so'ralmagan qaytarib bo'lmaydigan ishlarni (o'chirish, xat yuborish) qilishdan oldin sizdan so'rash buyurilgan. Shunday bo'lsa ham muhim ma'lumotlar ochiq turgan oynalarni yopib qo'ying va natijani tekshiring.
- Muhim jadvallar bilan ishlashdan oldin nusxa oling (Google Sheets'da **File → Make a copy**) yoki keyin **Version history** orqali qaytarishingiz mumkinligini yodda tuting.
- Ekrandagi har bir rasm Anthropic serverlariga yuboriladi.

## Muammolar

| Muammo | Yechim |
|---|---|
| `install.bat` "Python topilmadi" deydi | Python'ni qayta o'rnating va "Add python.exe to PATH" belgisini qo'ying, kompyuterni qayta yoqing. |
| "API kalit noto'g'ri" | Kalitni Console'dan qayta nusxalang, bo'sh joy qolmaganini tekshiring. |
| "Ruxsat yo'q" yoki 400 xato | Balans to'ldirilganini tekshiring. Boshqa model tanlab ko'ring. |
| Claude noto'g'ri joyni bosadi | Windows **Display → Scale** 100% yoki 125% bo'lsin, faqat bitta monitor ishlatilsin (dastur asosiy monitorni ko'radi). Skrinshot o'lchamini oshirib ko'ring. |
| O'zbekcha/kirillcha matn yozilmaydi | Bunday matn bufer (Ctrl+V) orqali qo'yiladi; maydon Ctrl+V'ni qabul qilishini tekshiring. |
| Qadamlar chegarasiga yetdi | Chat'ga `davom et` deb yozing yoki Sozlamalarda chegarani oshiring. |

## Fayllar tuzilishi

```
main.py                  dasturni ishga tushirish
install.bat / run.bat    Windows uchun o'rnatish va ishga tushirish
assistent/gui.py         oyna: Chat, Tezkor vazifalar, Sozlamalar
assistent/agent.py       Claude bilan ishlash sikli (computer use)
assistent/computer.py    skrinshot, sichqoncha, klaviatura boshqaruvi
assistent/attachments.py biriktirilgan fayllarni tayyorlash
assistent/tasks_store.py tezkor vazifalarni saqlash (tasks.json)
assistent/config.py      sozlamalar (config.json)
```

Texnik tafsilot: dastur `claude-opus-5-5` modelini `computer_toolset_20260801` asbobi bilan ishlatadi (Anthropic Python SDK 2.10+).
