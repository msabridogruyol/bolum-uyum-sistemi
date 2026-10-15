# Translation brief: Filizyol UI catalogue

Filizyol is a Turkish web app for high-school students (age 14–18), their school counsellors and school administrators. It helps students choose a university major ("bölüm"). Users take self-assessment questionnaires, explore majors and careers, track practice exams for the Turkish university entrance exam, and get coaching tips from a friendly mascot called "Filiz".

You translate Turkish source strings into ONE target language, which is given in your task.

## Input
A JSON array of objects `{i, tr, tur, yer}`:
- `i` = id.
- `tr` = Turkish source string.
- `tur` = kind:
  - `arayuz`: UI label or message.
  - `icerik`: coaching content.
  - `soru`: assessment question or answer option.
  - `etiket`: name of a major, trait, topic or occupation.
- `yer` = the source file. Use it only as context.

## Output
Write JSON objects that map `"<i>": "<translation>"` to files named `<OUTDIR>/<chunk>_<k>.json`, where k = 0,1,2,…
- Write about 250 entries per file, and write the files one after another with the Write tool. Do NOT try to write everything in one call.
- Valid JSON, UTF-8. Escape inner double quotes as `\"`.
- Every id in the input must appear exactly once across your files.

## Rules
1. **Placeholders**: `{0}`, `{1}`, … must appear in the translation exactly as many times as in the source. You may reorder them to suit the target grammar. A placeholder stands for a runtime value: a number, a name, a major name or another phrase.
2. Keep these unchanged: emojis, arrows (→ ←), bullets (·, •), symbols (%, +, /, ✓), numbers, URLs, e-mail addresses and markdown (`**bold**`).
   - The Turkish percent sign comes before the number (`%40`). Use the target language's normal order (e.g. `40%`), but only when the number is literally in the string. Leave `%{0}` as `{0}%` in languages that put % after the number.
3. Do NOT translate these names: Filizyol, Filiz (the mascot's name), YKS, TYT, AYT, YDT, LGS, KPSS, ALES, YÖK, YÖK Atlas, ÖSYM, MEB, TÜİK, İŞKUR, SGK, KVKK, ISCO, O*NET, RIASEC, Holland, Big Five, SJT, K1–K5, Excel, CSV, PDF, LinkedIn, TÜBİTAK, or any brand or product name.
   - On first mention in a sentence, you may add a short gloss in parentheses for exam names only where the source itself explains them. Otherwise keep them bare.
4. Turkish institutions and proper names (school names, city names, university names) stay as they are.
5. Register: friendly, clear, and use the informal "you" toward the student (du/tu/ты/tú/tu/…), as the Turkish does ("sen").
   - Texts aimed at school staff and administrators in Turkish use the formal "siz" (e.g. "seçin", "yükleyin"). Use the formal register for those (Sie/vous/Вы/usted/Lei/…).
   - Choose the register from the Turkish verb forms.
6. Match length roughly. UI labels must stay short (buttons, tabs, column headers).
7. Strings may be fragments, because a sentence can be split around a bold word or a link. Translate the fragment so it can join neighbouring fragments naturally. Keep leading or trailing punctuation and spaces.
8. Single Turkish words that are clearly keywords (e.g. a list of occupation words used for search) should also be translated as single words.
9. `tur: "soru"` (assessment items):
   - Translate faithfully and neutrally. Do not add, soften or intensify meaning.
   - Keep the first-person voice ("I enjoy…").
   - Keep Likert answer options short and parallel (e.g. "Strongly disagree … Strongly agree").
   - These are psychometric items, so preserve the exact construct.
10. If the source is just a code, an abbreviation, a number, or something already in a non-Turkish language (e.g. "WSM", "P8", "POST", "CSV"), copy it unchanged.
11. Glossary. Use these consistently in your target language; the English is given as the meaning:
    - bölüm → university major/degree programme
    - meslek → occupation
    - katman → layer (assessment layer K1–K5)
    - değerlendirme → assessment
    - deneme (sınavı) → practice exam
    - net → net score (correct minus penalised wrong answers)
    - okul yetkilisi → school administrator
    - rehber öğretmen / rehberlik → school counsellor / guidance counselling
    - koç / koçluk → coach / coaching
    - şube → class section (e.g. 12-A)
    - sınıf → grade/class (e.g. 12th grade)
    - uyum → fit/match (major fit %)
    - güçlü yön → strength
    - gelişime açık → area for growth
    - tercih → university preference list
    - puan türü → score type (SAY, EA, SÖZ, DİL — keep these codes)
    - sözlük → glossary
    - görev → task
    - seri → streak
    - çevrim içi → online
    - hedef bölüm → target major
    - kulüp → club
    - mezun → graduate/alumni

Work through the whole input. At the end, reply with only:
- the number of entries written;
- the file names.
