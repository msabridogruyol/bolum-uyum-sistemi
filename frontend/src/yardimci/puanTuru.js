// [2026-11-02] Bölümün puan türü "Değişken" ise (üniversiteye / programa göre farklı) öğrenciye açık bir ifadeyle gösterilir.
export const puanTuruMetni = (p) => (p && String(p).trim().toLocaleLowerCase('tr').startsWith('değişken') ? 'Üniversiteye göre değişir' : p)
