# Review brief: assessment question translations (meaning first)

Filizyol is a career-guidance app for Turkish high-school students (age 14–18). Its assessment uses situational-judgement questions: a short everyday situation plus 4 answer options. The student picks the option that fits them MOST and the one that fits them LEAST. Every option reflects a different value or motivation, for example recognition, helping others, autonomy, security, creativity, income, structure or learning.

You get a JSON array of `{i, tr, ceviri, yer}`:
- `tr` is the Turkish original.
- `ceviri` is the current translation into your target language.
- `yer` is `db:sorular` for the situation/question stem, or `db:soru_secenekleri` for an answer option.

## Goal
The student must understand **exactly the same meaning and the same underlying motivation** as a Turkish student. Translate by meaning, not word for word.

1. **Meaning and motivation.** Each option's motive must stay recognisable and distinct from the other options. Do not soften, intensify, moralise or make an option sound more or less socially desirable than the Turkish one.
2. **Natural, idiomatic language** for a teenager in that language.
   - Use the informal "you" (or the language's equivalent for students).
   - Options are written in the first person or as noun phrases, exactly as the Turkish is.
3. **Culture-specific details.** Adapt them only when a literal rendering would confuse; otherwise keep them. Examples:
   - "bahar şenliği" → the school's spring festival.
   - "dershane" → a private exam-prep course.
   - "YKS" stays YKS.
   - Turkish lira amounts stay as they are.
4. **Same length and register** as the source, roughly. Keep emojis, numbers and {0} placeholders.
5. **Do not change correct translations.** Only fix real problems:
   - wrong or shifted meaning, or a lost nuance that changes the motive;
   - a literal calque that reads unnaturally;
   - a wrong register;
   - an untranslated word, a typo or a grammar error.

## Output
Write ONLY the entries you changed to the output file as a JSON object `{"<i>": "<improved translation>"}`. Write it with the Write tool or Python, UTF-8. If nothing needs changing, write `{}`.

Read the whole input in parts (offset/limit). Keep stems and their options consistent with each other.

At the end, reply with:
- the number of entries changed;
- 3 short examples of the kind of issue you fixed.
