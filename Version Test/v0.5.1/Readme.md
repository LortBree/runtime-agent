# LAPORAN BASELINE ENTITY CORE — V0.5.1

## 1. Ringkasan Eksekutif

Baseline V0.5.1 telah berhasil menjalankan **500 cycle penuh tanpa kematian entity**. Run menggunakan initial state `hunger=60`, `thirst=60`, `energy=60`, `curiosity=50`, dengan seed `42`. Entity mencapai 101 simulated days dan membentuk 24 LR cells.

Secara survival, baseline berhasil:

> **Alive = True setelah 500 cycle.**

Namun secara perilaku, ditemukan pola dominan yang sangat kuat: **409 dari 500 action adalah `sleep`**, sedangkan hanya 11 `eat`, 12 `drink`, 67 `work`, dan 1 `idle`.

Trace menunjukkan bahwa penyebab utamanya bukan kegagalan learning atau context churn, melainkan kondisi Decision ketika tidak ada action dengan positive score. Pada kondisi tersebut, `sleep` berkali-kali dipilih dengan **score tepat 0.0** sebagai `"highest current-context known score"`.

Dengan demikian, V0.5.1 dapat dianggap sebagai **baseline fungsional tetapi memiliki policy pathology pada zero-utility regime**.

---

# 2. Tujuan Baseline

Baseline ini digunakan sebagai keadaan referensi sebelum perubahan policy berikutnya.

Pipeline Layer 3 berjalan dalam urutan:

```text
Observe
    ↓
Retrieve Knowledge
    ↓
Decision
    ↓
Execute
    ↓
Observe S'
    ↓
Generate Experience
    ↓
Learn Relation
    ↓
Update Knowledge
```

Urutan tersebut memang diterapkan di `EntityCore.cycle()`: environment dieksekusi terlebih dahulu, kemudian experience dibuat dari transition aktual, dan setelah itu knowledge diperbarui.

Arsitektur ini penting karena LR belajar dari **transition aktual**, bukan konsekuensi action yang diasumsikan sebelumnya.

---

# 3. Layer 1 — Environment

State terdiri dari:

```text
hunger
thirst
energy
curiosity
alive
```

Action yang tersedia:

```text
eat
drink
sleep
work
idle
```

Entity memulai pada:

```text
hunger   = 60
thirst   = 60
energy   = 60
curiosity= 50
```

dan pada akhir 500 cycle:

```text
hunger   = 22.0
thirst   = 37.5
energy   = 100.0
curiosity= 51.5
alive    = True
```

---

# 4. Layer 2 — Knowledge

Knowledge direpresentasikan sebagai relation conditioned terhadap state context, action, dan variable. Pada implementasi LR, evidence semantic di-_decay_ dengan `gamma`, kemudian evidence dari observation terbaru ditambahkan. Dominant magnitude dipilih dari evidence terbesar. Confidence dihitung dari support versus contradiction, kemudian dipetakan menjadi `unknown`, `may`, atau `should`.

Secara konseptual:

$$
count_m^{t}

\gamma count_m^{t-1}  
+  
I(m=m_{observed})  
$$

Kemudian:

$$ 
confidence

\frac{support+\alpha}  
{support+contradiction+2\alpha}  
$$

Implementasi juga menggunakan delta aktual:

$$
\Delta_v = S'_{v}-S_v  
$$

kemudian delta tersebut diubah menjadi semantic effect bucket.

Ini terbukti penting pada eksperimen saturation sebelumnya: ketika action `drink` terus dijalankan pada `thirst=0`, observasi aktual menjadi `NONE`, dan LR berubah dari `DEC_LARGE` menjadi `NONE`.

---

# 5. Decision Layer

Decision mengevaluasi action berdasarkan urgency, learned effect, dan confidence. Source snapshot V0.5.1 mendokumentasikan prinsip:

$$
Score

Urgency  
\times  
LearnedEffect  
\times  
Confidence  
$$

dengan arah benefit:

```text
hunger   : decrease beneficial
thirst   : decrease beneficial
energy   : increase beneficial
curiosity: increase beneficial
```

Urgency sendiri dihitung dari nilai state aktual: hunger/thirst semakin tinggi semakin urgent, sedangkan energy/curiosity semakin rendah semakin urgent.

Unknown relation tidak dianggap sebagai efek negatif; ia diperlakukan sebagai unknown.

Exploration V0.5.1 bersifat sederhana dan deterministic terhadap unknown actions, bukan RL atau epsilon-greedy.

---

# 6. Hasil 500 Cycle

## Survival

|Metrik|Hasil|
|---|--:|
|Total cycle|500|
|Simulated days|101|
|Alive|True|
|LR cells|24|

## Decision mode

|Mode|Count|
|---|--:|
|Explore|5|
|Exploit|495|
|Fallback|0|

Artinya setelah cold-start selesai, entity hampir sepenuhnya masuk mode exploitation.

## Action distribution

|Action|Count|Proporsi|
|---|--:|--:|
|sleep|409|81.8%|
|work|67|13.4%|
|drink|12|2.4%|
|eat|11|2.2%|
|idle|1|0.2%|

Data count berasal langsung dari summary baseline.

---

# 7. Context Behavior

Hanya **5 dari 16 possible state contexts** yang dikunjungi selama 500 cycle.

Context paling dominan:

```text
(LOW, LOW, HIGH, HIGH)
```

muncul 410 kali.

Context lainnya:

```text
(LOW, LOW, HIGH, LOW)   67
(LOW, HIGH, HIGH, HIGH) 12
(HIGH, LOW, HIGH, HIGH) 8
(HIGH, HIGH, HIGH, HIGH) 3
```

Context transition juga menunjukkan self-loop yang sangat besar:

```text
(LOW,LOW,HIGH,HIGH)
→
(LOW,LOW,HIGH,HIGH)
= 343 kali
```

Total context changes adalah 157 dari 500 cycle, atau 31.4%.

### Interpretasi

Ini berarti **context churn ada, tetapi bukan penjelasan utama sleep dominance**. Sebagian besar waktu entity justru berada pada satu context yang sama.

---

# 8. Evidence Maturity

Instrumentasi baseline menunjukkan kualitas evidence relation yang digunakan ketika action dipilih.

|Action|Uses|Mean support|Mean confidence|
|---|--:|--:|--:|
|eat|9|3.146|0.781|
|drink|11|5.104|0.837|
|sleep|408|18.329|0.913|
|work|66|14.437|0.926|

Temuan utama:

> `sleep` **bukan** dipilih karena relation-nya masih miskin.

Sebaliknya, relation `sleep` yang digunakan rata-rata sangat matang.

---

# 9. Bukti Langsung Sleep Lock

Pada fase awal, `sleep` memang mempunyai positive score.

Contohnya cycle 4:

```text
sleep score = 1.333
```

dengan relation `energy → INC_LARGE`. Trace menunjukkan support sekitar 1 dan confidence sekitar 0.667 pada awal pembelajaran.

Setelah beberapa cycle, LR belajar bahwa dalam context dominan, `sleep` tidak lagi menghasilkan benefit pada beberapa variable. Pada cycle berikutnya score akhirnya menjadi:

```text
sleep = 0.0
```

namun action tersebut masih dipilih.

Contoh konkret: pada cycle 10, state sebelum action memiliki:

```text
hunger = 36
thirst = 35
energy = 100
```

namun decision tetap memilih:

```text
sleep
score = 0.0
reason = highest current-context known score
```

Artinya Decision tidak menyatakan bahwa `sleep` memiliki utility positif. Ia memilih `sleep` karena tidak ada known current-context action yang lebih baik.

---

# 10. Zero-Score Regime

Analisis trace menemukan **405 cycle dengan decision score tepat 0.0**.

Distribusinya sangat ekstrem:

```text
sleep = 404
eat   = 1
drink = 0
work  = 0
idle  = 0
```

Ke-404 kasus `sleep` tersebut tercatat sebagai:

```text
mode   = exploit
score  = 0.0
reason = highest current-context known score
```

Satu kasus zero-score non-sleep adalah `eat`, dengan reason:

```text
action known globally; current context unknown
```

Dengan demikian:

$$
\frac{405}{500}=81.0%  
$$

seluruh cycle berada pada zero-score regime.

Sedangkan:

$$
\frac{404}{500}=80.8%  
$$

merupakan `sleep` dengan score `0`.

Ini adalah temuan utama baseline V0.5.1.

---

# 11. Diagnosis

Berdasarkan kombinasi source code dan trace, tiga hipotesis berikut dapat ditolak sebagai penyebab utama:

### Sparse knowledge

**Tidak didukung.**

`Sleep` digunakan dengan mean support `18.329` dan mean confidence `0.913`.

### Context churn

**Bukan penyebab dominan.**

Satu context dikunjungi 410 kali dan terdapat 343 self-loop pada context tersebut.

### LR gagal adaptasi

**Tidak didukung.**

Eksperimen saturation sebelumnya menunjukkan LR dapat mengubah relation `DEC_LARGE → NONE` berdasarkan observation aktual dan mencapai confidence `0.932`, label `should`.

### Temuan yang didukung data

Masalahnya berada pada **decision semantics ketika seluruh known action memiliki score non-positive**.

Secara abstrak:

$$
\max_a Score(a|S)\le0  
$$

Namun policy tetap memilih action dengan score terbesar. Dalam baseline, action tersebut hampir selalu `sleep`.

Jadi terjadi:

```text
positive score
    ↓
exploit

tidak ada positive score
    ↓
best known score = 0
    ↓
sleep
```

Bukan:

```text
sleep dianggap bagus
```

melainkan:

```text
sleep adalah known action dengan score tertinggi ketika utility positif habis
```

---

# 12. Keterbatasan Baseline

Baseline ini berhasil membuktikan survival dan learning, tetapi belum dapat dianggap sebagai policy yang balanced.

Keterbatasan utama:

1. **Zero-score attractor** — ketika tidak ada action positif, policy dapat mengulang action dengan score 0.
    
2. **Action distribution sangat skewed** — `sleep` mencapai 81.8%.
    
3. **Exploration cepat habis** — hanya 5 dari 500 cycle merupakan exploration.
    
4. **Context coverage rendah** — hanya 5/16 contexts yang dikunjungi.
    

Namun poin-poin tersebut adalah **karakteristik baseline**, bukan alasan untuk langsung mengubah V0.5.1.

---

# 13. Status V0.5.1

|Komponen|Status|
|---|---|
|Environment transition|✅|
|Experience generation|✅|
|LR evidence accumulation|✅|
|Evidence decay|✅|
|Confidence|✅|
|Semantic label|✅|
|Environment-shift adaptation|✅|
|Saturation self-correction|✅|
|Decision scoring|✅|
|500-cycle survival|✅|
|Balanced action selection|⚠️|
|No-positive policy semantics|⚠️|

Baseline menghasilkan bukti bahwa **mekanisme learning sudah berjalan**, tetapi **selection policy memiliki regime yang belum terdefinisi dengan baik ketika expected benefit tidak positif**.

---

# 14. Kesimpulan

V0.5.1 dapat diringkas sebagai:

> **Learning layer berhasil, survival berhasil, tetapi policy selection belum memiliki aturan eksplisit untuk kondisi ketika semua learned action memiliki non-positive score.**

Temuan ini penting karena kita sekarang tidak lagi menebak-nebak sumber masalah. Trace menunjukkan secara langsung bahwa 404 dari 500 cycle adalah `sleep` dengan score `0.0`, dan `sleep` tersebut umumnya didukung oleh relation yang justru sudah matang.

Karena itu, **V0.5.1 layak dibekukan sebagai baseline**. Perubahan berikutnya harus dianggap sebagai perubahan policy baru, bukan patch terhadap baseline.

### Baseline reference

```text
Version           : V0.5.1
Cycles            : 500
Seed              : 42
Alive             : True
Simulated days    : 101
LR cells          : 24
Explore           : 5
Exploit           : 495

eat               : 11
drink             : 12
sleep             : 409
work              : 67
idle              : 1

Zero-score cycles : 405
Sleep @ zero      : 404
Context changes   : 157
Unique contexts   : 5
```

**Catatan sumber:** laporan ini membedakan data eksperimen 500-cycle yang aktual dari source snapshots yang tersedia di percakapan. Beberapa source snapshot lama menunjukkan evolusi implementasi Decision, jadi saya tidak memperlakukan source snapshot yang tidak identik dengan trace final sebagai bukti perilaku final. Data perilaku final diambil dari `baseline_500_summary.txt` dan `baseline_500_trace.json`.