# ENTITY CORE — GLOSSARY

## A

**Action**  
Perilaku yang dapat dipilih dan dieksekusi Entity. Pada eksperimen saat ini action yang tersedia adalah `eat`, `drink`, `sleep`, `work`, dan `idle`.

**Action Known**  
Status yang menunjukkan bahwa suatu action **pernah diamati di setidaknya satu state context**. Ini berbeda dari `Context Known`: sebuah action bisa known secara global tetapi belum memiliki relation pada context saat ini.

**Action Score**  
Nilai numerik yang digunakan Decision untuk menilai action berdasarkan relation yang tersedia pada current context.

---

## B

**State Bucket**  
Representasi diskrit dari state aktual. Setiap state variable dipetakan menjadi `LOW` atau `HIGH` menggunakan batas 50.

Contoh:

```text
(hunger=60, thirst=30, energy=60, curiosity=50)
→
(HIGH, LOW, HIGH, HIGH)
```

State bucket menjadi bagian dari key relation di Knowledge Layer.

**Bucket Transition**  
Perubahan dari state bucket sebelum action ke state bucket setelah action.

```text
(HIGH,LOW,HIGH,HIGH)
→
(LOW,LOW,HIGH,HIGH)
```

---

## C

**Confidence**  
Ukuran seberapa kuat evidence saat ini mendukung magnitude yang dipelajari.

Dalam Knowledge Layer, confidence berasal dari perbandingan evidence yang mendukung relation terhadap contradiction/evidence lawan.

Confidence **bukan utility**.

Confidence tinggi berarti:

> “Saya cukup yakin relation ini benar.”

Bukan:

> “Action ini bagus.”

---

**Context**  
State bucket yang sedang aktif ketika action dievaluasi.

Contoh:

```text
Context =
(LOW, LOW, HIGH, HIGH)
```

**Context Known**  
Menunjukkan bahwa action memiliki setidaknya satu relation yang diketahui pada **current state context**.

Ini berbeda dari `Action Known`.

---

**Context Churn**  
Frekuensi state context berubah sepanjang run.

Pada baseline 500-cycle V0.5.1, context change terjadi 157 kali; pada V0.5.2 hanya 4 kali.

---

## D

**Decision**  
Hasil akhir proses pemilihan action. Decision memiliki action, mode, score, reason, dan evaluasi action.

**Decision Engine**  
Komponen Layer 3 yang:

1. menghitung score action;
    
2. mengevaluasi current-context knowledge;
    
3. menentukan apakah action dieksploitasi atau dieksplorasi.
    

Pada V0.5.1 dan V0.5.2, perubahan policy terjadi di selection layer, bukan Knowledge Layer.

---

**Desirability**  
Arah keuntungan atau kerugian magnitude terhadap kualitas survival.

Contoh:

```text
hunger:
DEC_LARGE → desirable
INC_LARGE → undesirable

energy:
INC_LARGE → desirable
DEC_LARGE → undesirable
```

Desirability bukan confidence dan bukan urgency.

---

## E

**Evidence**  
Bobot informasi empiris yang mendukung relation.

Evidence berasal dari **observasi transition aktual**, bukan dari nilai nominal action.

Secara konseptual:

```text
state_before
→ action
→ state_after
→ delta aktual
→ observed effect
→ evidence update
```

Evidence lama mengalami decay, sedangkan observasi baru menambah evidence.

**Evidence Maturity**  
Derajat kematangan knowledge relation yang diaproksimasi melalui jumlah/berat evidence yang sudah terkumpul.

Semakin besar evidence, semakin matang relation.

---

**Explore / Exploration**  
Mode pengambilan action ketika agent tidak menemukan positive current-context score dan memilih action untuk memperoleh pengalaman tambahan.

Pada V0.5.2 exploration menggunakan novelty berbasis evidence maturity.

---

**Exploration Lock**  
Pathology yang ditemukan di V0.5.2: exploration tetap dilakukan meskipun knowledge sudah sangat matang.

Contoh trace menunjukkan action `work` tetap dipilih sebagai `explore` walaupun evidence-nya sekitar 16 dan confidence sekitar 0.945.

---

**Exploit / Exploitation**  
Mode pengambilan action ketika tersedia positive current-context score.

Decision memilih action dengan positive score tertinggi.

---

## L

**Learned Relation**  
Pengetahuan empiris tentang dampak sebuah action terhadap state variable dalam context tertentu.

Secara konseptual:

```text
(context, action, variable)
→
magnitude
confidence
support
contradiction
```

Contoh:

```text
(LOW,LOW,HIGH,HIGH)
+
drink
+
thirst
→
DEC_LARGE
```

---

## M

**Magnitude**  
Kategori diskrit yang menggambarkan arah dan besar perubahan state variable:

```text
DEC_LARGE
DEC_SMALL
NONE
INC_SMALL
INC_LARGE
```

Magnitude adalah hasil pembelajaran dari delta aktual.

**Mean / Mean Delta**  
Istilah ini perlu dijaga agar tidak tercampur dengan `magnitude`. Pada desain V0.5.1 yang sekarang dipakai, Decision menggunakan magnitude + confidence untuk scoring. Jangan menganggap `mean_delta` sebagai pengganti learned relation tanpa definisi eksplisit.

---

## N

**Novelty**  
Ukuran seberapa belum matangnya knowledge terhadap suatu action.

Pada `ExplorationPolicy` V0.5.2:

$$
Novelty(E)=\frac{k}{E+k}  
$$

dengan (E) = evidence dan `k=5.0` pada eksperimen.

Karakteristik:

```text
E tinggi → novelty rendah
E rendah → novelty tinggi
```

Novelty **bukan utility**.

Novelty menjawab:

> “Seberapa banyak lagi yang mungkin kita pelajari?”

Bukan:

> “Seberapa bagus action ini?”

---

## P

**Positive Score**  
Score action yang:

$$
Score > 0  
$$

Positive score menandakan action memiliki predicted net contribution yang menguntungkan menurut Decision scoring saat ini.

**No-Positive Regime**  
Kondisi ketika:

$$
\max_a Score(a|S)\le0  
$$

Ini menjadi titik penting evolusi policy:

```text
V0.5.1:
no-positive → best known action

V0.5.2:
no-positive → exploration
```

---

## R

**Relation**  
Unit knowledge yang menghubungkan:

```text
state context
+
action
+
state variable
```

dengan learned effect.

**Support**  
Bobot evidence yang mendukung magnitude tertentu.

**Contradiction**  
Bobot evidence yang mendukung magnitude berlawanan dibanding magnitude dominan.

Support dan contradiction digunakan dalam pembentukan confidence.

---

## S

**Score**  
Nilai utility-like yang digunakan Decision untuk membandingkan action.

Pada V0.5.1/V0.5.2 secara konseptual:

$$
Score(a|S)

\sum_v  
ContextWeight(S_v,v)  
\times  
Desirability(v,m)  
\times  
Confidence  
$$

Score positif → action kandidat exploit.

Score nol → tidak memberikan benefit net.

Score negatif → predicted harmful.

**Score Zero**  
Kondisi:

$$ 
Score=0  
$$

Ini sangat penting dalam diagnosis V0.5.1 karena `sleep` sering dipilih dengan score `0.0`.

**Sleep Lock**  
Pathology V0.5.1 ketika `sleep` berulang kali dipilih sebagai known action dengan score zero karena tidak ada positive current-context alternative.

Baseline menghasilkan 409 `sleep` dari 500 cycle.

---

## U

**Urgency**  
Bobot yang menggambarkan seberapa mendesak suatu state variable untuk diperbaiki.

Contoh:

```text
hunger tinggi
→ urgency tinggi

energy rendah
→ urgency tinggi
```

Urgency berbeda dari confidence dan novelty.

---

## V

**Variable / State Variable**  
Komponen state yang diamati dan dipelajari:

```text
hunger
thirst
energy
curiosity
```

---

# 5 Istilah yang Harus Jangan Tertukar

|Istilah|Pertanyaan yang dijawab|
|---|---|
|**Score**|“Seberapa baik action ini sekarang?”|
|**Confidence**|“Seberapa yakin kita terhadap relation?”|
|**Evidence**|“Seberapa banyak pengalaman mendukung relation?”|
|**Novelty**|“Seberapa belum matangnya knowledge?”|
|**Urgency**|“Seberapa mendesak variable ini diperbaiki?”|

Contoh:

```text
sleep
score      = 0
confidence = 0.95
evidence   = 20
novelty    = rendah
urgency    = rendah
```

Interpretasinya **bukan** “sleep bagus”.

Interpretasinya:

> Knowledge tentang sleep sudah matang, tetapi pada state tersebut sleep tidak memberikan positive utility.

---

# Version-specific Terms

### V0.5.1 — Zero-Score / Sleep Lock

```text
positive score
→ exploit

no positive
→ best known current-context action
```

Hasil baseline:

```text
sleep = 409 / 500
zero-score sleep = 404
```

### V0.5.2 — Novelty Exploration

```text
positive score
→ exploit

no positive
→ novelty-based exploration
```

Hasil baseline:

```text
explore = 397 / 500
sleep = 98
```

Tetapi muncul:

```text
exploration saturation
```

karena exploration tetap aktif walaupun evidence sudah matang.

---

## Prinsip Dokumentasi

Untuk versi berikutnya, setiap perubahan policy sebaiknya dijelaskan dalam format:

```text
Condition
→ Decision regime
→ Formula
→ Expected behavior
→ Failure mode
→ Evidence from experiment
```

Dengan begitu istilah **exploit**, **explore**, **novelty**, **neutral**, dan **least-harm** tidak berubah arti hanya karena versi algoritma berubah.