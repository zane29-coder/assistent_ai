# Assistent AI — kompyuter ekranini boshqaruvchi yordamchi

Bu dastur Claude'ning **computer use** imkoniyati yordamida kompyuteringiz ekranini ko'radi va sichqoncha hamda klaviaturani o'zi boshqarib, siz bergan ishni bajaradi. Masalan, Chrome'da ochiq Google Sheets jadvalidagi `#REF!` xatolarini topib tuzatishi mumkin.

Claude Pro tarifi **kerak emas**. Dastur to'g'ridan-to'g'ri Anthropic API bilan ishlaydi, faqat API kalit kerak bo'ladi.

## Ikki xil ishlash usuli

1. **Chat.** Vazifani oddiy so'z bilan yozasiz, masalan "Chrome'ni och va ob-havoni ko'rsat". Claude ekranni boshqarib bajaradi, kerak bo'lsa sizdan savol so'raydi, siz javob yozib suhbatni davom ettirasiz. Chatga fayl ham biriktirish mumkin.
2. **Tezkor vazifalar.** Doimiy qilinadigan ishlar uchun bir marta **head prompt** (batafsil ko'rsatma) yozib, kerakli fayllarni biriktirib saqlab qo'yasiz. Keyin ro'yxatdan tanlab **▶ Ishga tushirish** tugmasini bosasiz (yoki ikki marta bosasiz). Natija Chat oynasida ko'rinadi va xohlasangiz o'sha yerda davom ettirasiz.

Dasturda namuna sifatida **"Google Sheets: #REF! xatolarini tuzatish"** vazifasi tayyor turadi.

## Eng oson yo'l: tayyor .exe (hech narsa o'rnatish shart emas)

1. **[AssistentAI.exe ni yuklab oling](https://github.com/zane29-coder/assistent_ai/releases/download/latest/AssistentAI.exe)**.
2. Faylni ikki marta bosing. Windows "Windows protected your PC" deb ogohlantirsa, **More info → Run anyway** ni bosing (dastur imzolanmagani uchun shunday chiqadi).
3. Birinchi ochilganda dastur API kalit olish yo'lini ko'rsatadi: saytda kalit oling, dasturga qo'yib **Saqlash** ni bosing.
4. Tayyor, **Chat** yoki **Tezkor vazifalar** bo'limidan foydalaning.

Python ham, boshqa dastur ham kerak emas. Sozlamalar va vazifalar `%APPDATA%\AssistentAI` papkasida saqlanadi, shuning uchun .exe ni yangisiga almashtirsangiz ham ular yo'qolmaydi. .exe har safar kod yangilanganda GitHub tomonidan avtomatik qayta yig'iladi.

Quyidagi bo'limlar dasturni manba koddan ishga tushirmoqchi bo'lganlar uchun.

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

Vazifa ishlayotganda asosiy oyna yashiriladi (ekranni to'smasligi uchun) va dastur tezkor tugmalar orqali boshqariladi. Ish tugagach qisqa ovoz chiqadi, asosiy oyna qaytadi va barcha qadamlar Chat'da ko'rinadi.

## Tezkor tugmalar

Ular butun Windows bo'ylab ishlaydi: Chrome yoki boshqa dastur ochiq turganda ham, klaviatura lotin yoki kirill tilida bo'lsa ham.

| Tugma | Nima qiladi |
|---|---|
| **Ctrl+Alt+S** | Tezkor vazifalar ro'yxatida tanlangan vazifani boshlaydi |
| **Ctrl+Alt+P** | Pauza. Claude to'xtab turadi, siz sichqoncha va klaviaturadan bemalol foydalanasiz. Yana bosilsa davom etadi va ekranni qaytadan ko'rib oladi |
| **Ctrl+Alt+R** | Claude'ga hozirgi ekran rasmini yuboradi (pauzada bo'lsa, shu rasm bilan davom ettiradi). Vazifa ishlamayotganda bosilsa, ekran rasmini Chat'ga biriktiradi va oynani ochadi, siz faqat savolingizni yozasiz |
| **Ctrl+Alt+X** | Vazifani to'xtatadi |
| **Ctrl+Alt+L** | Maxfiylik chegarasi: AI ko'rishi mumkin bo'lgan joyni belgilash (pastga qarang) |

Har bir tugma bosilganda qisqa ovoz eshitiladi. Tugmalarni `%APPDATA%\AssistentAI\config.json` faylidagi `hotkey_start`, `hotkey_pause`, `hotkey_screenshot`, `hotkey_stop` qatorlarida o'zgartirish mumkin (masalan `"ctrl+alt+f9"`).

### #REF! xatolarini tuzatish

1. Chrome'da Google Sheets jadvalingizni oching va oynani ochiq qoldiring.
2. **Tezkor vazifalar** → **"Google Sheets: #REF! xatolarini tuzatish"** → **▶ Ishga tushirish**.
3. Kerak bo'lsa, **qo'shimcha izoh** maydoniga masalan `faqat "Hisobot" varag'ini tekshir` deb yozing.

Maslahat: agar jadvalning eski to'g'ri nusxasi yoki ustunlar tavsifi bo'lsa, uni `.xlsx`, `.csv` yoki skrinshot ko'rinishida vazifaga biriktiring. Claude to'g'ri havolani aniqlashda undan foydalanadi.

### O'z tezkor vazifangizni qo'shish

**+ Yangi vazifa** → nom va head prompt yozing → kerak bo'lsa fayl qo'shing → **Saqlash**. Head promptni qanchalik aniq yozsangiz, natija shunchalik yaxshi bo'ladi: qaysi dastur yoki sayt, qaysi tartibda ishlash kerak, nimalarga tegmaslik kerak va oxirida qanday hisobot berish kerakligini yozing. Vazifalar `tasks.json` faylida saqlanadi.

Biriktirilgan fayl kompyuterda ochilmaydi: uning ichidagi ma'lumot to'g'ridan-to'g'ri Claude'ga yuboriladi. Claude faylni o'zi tahlil qiladi, ekrandan esa faqat vazifaning o'zini bajarish uchun foydalanadi. Qo'llab-quvvatlanadigan fayllar:

- Word (`.docx`), PowerPoint (`.pptx`)
- Excel (`.xlsx`, `.xlsm` formulalari va qiymatlari bilan, `.xls`), `.csv`
- PDF, rasmlar (png, jpg, webp, gif, bmp)
- matnli fayllar (txt, json, md va boshqalar)

Eski `.doc` yoki `.ppt` fayllarni avval Word yoki PowerPoint'da `.docx` / `.pptx` qilib saqlab oling.

## Maxfiylik chegarasi (Ctrl+Alt+L)

Ekranda shaxsiy ma'lumot (xabarlar, bank, boshqa oynalar) bo'lsa, AI'ga faqat kerakli qismni ko'rsating:

1. **Ctrl+Alt+L** ni bosing (yoki **Sozlamalar → Chegarani belgilash**). Ekran xiralashadi.
2. Sichqoncha bilan AI ishlashi kerak bo'lgan joyni to'rtburchak qilib chizing va qo'yib yuboring.
3. Shu joy atrofida **qizil chiziq** paydo bo'ladi va u doim ko'rinib turadi.

Shundan keyin:

- AI'ga yuboriladigan har bir ekran rasmi **faqat qizil chiziq ichidan** olinadi. Tashqaridagi narsa umuman suratga olinmaydi va hech qayerga yuborilmaydi.
- Sichqoncha bilan bosish, sudrash va aylantirish faqat chiziq ichida bajariladi. AI tashqaridagi joyni bosmoqchi bo'lsa, dastur buni rad etadi.
- Chegara saqlanib qoladi. O'zgartirish uchun yana Ctrl+Alt+L bosib, qaytadan chizing. Olib tashlash uchun Ctrl+Alt+L, keyin **Delete** (yoki Sozlamalarda **Olib tashlash**). **Esc** bekor qiladi.

Bilish kerak: klaviatura chegara bilan cheklanmaydi. AI yozgan matn yoki bosgan tugma (masalan Ctrl+W) hozir faol turgan oynaga boradi. Shuning uchun ish boshlashdan oldin kerakli oyna (masalan Chrome) chegara ichida va faol bo'lsin.

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
- **Favqulodda to'xtatish**: **Ctrl+Alt+X** ni bosing yoki sichqonchani ekranning **chap-yuqori burchagiga** olib boring.
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
.github/workflows/       Windows .exe ni avtomatik yig'ish (PyInstaller)
install.bat / run.bat    Windows uchun o'rnatish va ishga tushirish
assistent/gui.py         oyna: Chat, Tezkor vazifalar, Sozlamalar
assistent/agent.py       Claude bilan ishlash sikli (computer use)
assistent/computer.py    skrinshot, sichqoncha, klaviatura boshqaruvi
assistent/hotkeys.py     butun tizim bo'ylab tezkor tugmalar (Windows)
assistent/region.py      maxfiylik chegarasini chizish va qizil chiziq
assistent/attachments.py biriktirilgan fayllarni tayyorlash
assistent/tasks_store.py tezkor vazifalarni saqlash (tasks.json)
assistent/config.py      sozlamalar (config.json)
```

Texnik tafsilot: dastur `claude-opus-5-5` modelini `computer_toolset_20260801` asbobi bilan ishlatadi (Anthropic Python SDK 2.10+).
