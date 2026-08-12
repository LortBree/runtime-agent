# LAPORAN EKSPERIMEN ENTITY CORE — V0.5.3

## 1. Ringkasan Eksekutif

V0.5.3 memperkenalkan **regime keputusan ketiga** setelah kelemahan V0.5.1 dan V0.5.2 ditemukan.

Policy V0.5.3:

$$
Score_{\max}>0  
\Rightarrow Exploit  
$$

$$
Score_{\max}\le0  
\land Novelty_{\max}>0.25  
\Rightarrow Explore  
$$

$$
Score_{\max}\le0  
\land Novelty_{\max}\le0.25  
\Rightarrow Neutral/Least\text{-}harm  
$$

Eksperimen 500 cycle menunjukkan seluruh mekanisme tersebut aktif dan berjalan tanpa entity mati. Entity menyelesaikan 500 cycle, mencapai 101 simulated days, dan membentuk 40 LR cells.

Namun hasil behavioral belum final. Exploration berhasil dibatasi, tetapi neutral regime kemudian menghasilkan **drink lock**: 350 dari 500 cycle masuk neutral, dan 326 dari 350 neutral action adalah `drink`.

Kesimpulan utama:

> **Saturation mechanism V0.5.3 berhasil. Least-harm computation juga bekerja secara matematis. Tetapi `argmin(harm)` belum cukup untuk mendefinisikan neutral policy, karena action dengan zero harm dapat menjadi attractor walaupun action tersebut tidak lagi diperlukan.**

---

# 2. Tujuan V0.5.3

V0.5.2 berhasil menghilangkan sleep lock V0.5.1, tetapi menghasilkan exploration yang terlalu dominan:

```text
Explore = 397 / 500
```

Tujuan V0.5.3 adalah menambahkan stopping condition untuk exploration sehingga agent tidak terus mengeksplorasi setelah knowledge menjadi matang.

Solusi yang diuji:

$$
N(E)=\frac{k}{E+k}  
$$

dengan:

$$
k=5  
$$

dan threshold:

$$
\tau=0.25  
$$

Dengan demikian:

$$
N(E)\le0.25  
\iff  
E\ge15  
$$

Evidence sekitar 15 atau lebih dianggap sudah memasuki saturation regime.

---

# 3. Perubahan Policy

V0.5.3 memperluas policy dari dua regime menjadi tiga.

### Regime 1 — Exploit

Jika terdapat positive current-context score:

$$
\max Score>0  
$$

maka dipilih action dengan score positif tertinggi.

### Regime 2 — Explore

Jika tidak ada positive score tetapi novelty masih tinggi:

$$
\max Score\le0  
\land  
\max Novelty>0.25  
$$

maka `ExplorationPolicy` memilih action dengan novelty tertinggi.

### Regime 3 — Neutral / Least-Harm

Jika positive score tidak ada dan novelty sudah saturated:

$$  
\max Score\le0  
\land  
\max Novelty\le0.25  
$$

maka dipilih action dengan predicted harm minimum:

$$  
a^*=\arg\min_a Harm(a|S)  
$$

---

# 4. Implementasi Least-Harm

Harm dipisahkan dari utility.

Utility tetap dihitung menggunakan machinery existing:

$$  
Contribution =  
ContextWeight  
\times  
Desirability  
\times  
Confidence  
$$

Sedangkan harm mengambil sisi negatif saja:

$$  
HarmContribution =  
ContextWeight  
\times  
\max(0,-Desirability)  
\times  
Confidence  
$$

Kemudian:

$$ 
Harm(a|S)

\sum_v HarmContribution_v  
$$

Tujuan neutral regime adalah memilih:

$$  
\arg\min Harm  
$$

Konsep ini berbeda dari sekadar memilih score terbesar ketika seluruh score non-positive.

---

# 5. Konfigurasi Eksperimen

| Parameter            | Nilai              |
| -------------------- | ------------------ |
| Version              | V0.5.3             |
| Total cycles         | 500                |
| Seed                 | 42                 |
| Initial hunger       | 60.0               |
| Initial thirst       | 60.0               |
| Initial energy       | 60.0               |
| Initial curiosity    | 50.0               |
| Novelty `k`          | 5.0                |
| Saturation threshold | 0.25               |
| Environment          | baseline           |
| Knowledge            | baseline mechanism |

Eksperimen menghasilkan 500 trace records.

---

# 6. Survival

Hasil survival:

```text
Alive          : True
Total cycles   : 500
Simulated days : 101
LR cells       : 40
```

Tidak ada fallback dan entity tidak mati selama eksperimen.

---

# 7. Final State

```text
Hunger       : 0.0
Thirst       : 0.0
Energy       : 100.0
Curiosity    : 94.0
```

State ini menunjukkan bahwa survival tetap tercapai, tetapi homeostasis belum ideal. Hunger dan thirst berada di floor, sementara energy berada di ceiling.

Dengan demikian, survival `True` **tidak cukup** untuk menyatakan policy sudah sehat.

---

# 8. Decision Regime Distribution

Hasil:

|Regime|Count|Persentase|
|---|--:|--:|
|Explore|116|23.2%|
|Exploit|34|6.8%|
|Neutral|350|70.0%|
|Fallback|0|0.0%|

Perubahan ini menunjukkan bahwa saturation mechanism memang mengurangi exploration secara drastis dibandingkan V0.5.2.

Perbandingan:

```text
V0.5.2 Explore = 397 / 500 = 79.4%
V0.5.3 Explore = 116 / 500 = 23.2%
```

Dengan demikian, **exploration saturation berhasil secara behavioral**.

---

# 9. Action Distribution

Action usage V0.5.3:

|Action|Count|
|---|--:|
|eat|43|
|drink|361|
|sleep|40|
|work|28|
|idle|28|

Distribusi ini sangat skewed ke `drink`.

Namun penyebabnya dapat dilokalisasi ke neutral regime.

---

# 10. Neutral Action Distribution

Neutral actions:

|Action|Count|
|---|--:|
|eat|13|
|drink|326|
|sleep|11|
|work|0|
|idle|0|

Dengan demikian:

$$
\frac{326}{350}=93.14%  
$$

seluruh neutral decisions memilih `drink`.

Ini adalah pathology utama V0.5.3.

---

# 11. Mengapa Drink Menang?

Least-harm objective menjawab:

> Action mana yang diprediksi menyebabkan kerusakan paling kecil?

Bukan:

> Action mana yang paling diperlukan sekarang?

Pada trace, neutral decision terhadap `drink` terjadi ketika:

```text
score       = 0.0
harm_score  = 0.0
context_known = true
```

Contoh menunjukkan `drink` telah memiliki evidence matang dan confidence tinggi, namun tetap mempunyai zero harm.

Pada bagian trace lain, evidence `drink` bahkan sudah mencapai sekitar 19 dan confidence sekitar 0.92, tetapi tetap dipilih neutral karena harm-nya nol.

Jadi:

$$  
Harm(drink)=0  
$$

membuat `drink` menjadi attractor neutral.

---

# 12. Bukti Saturation Berfungsi

Contoh trace menunjukkan:

```text
selected_evidence ≈ 15.48
selected_novelty ≈ 0.244
max_novelty ≈ 0.247
saturated = true
```

dan Decision berpindah ke:

```text
mode = neutral
reason = exploration saturated; selected least-harm action
```

Ini konsisten dengan threshold:

$$  
0.247 < 0.25  
$$

Dengan kata lain, **transition dari Explore → Neutral bekerja sesuai desain matematis**.

---

# 13. Evidence Maturity

Neutral decisions tidak terjadi karena knowledge masih kosong.

Contoh trace menunjukkan relation `drink` sudah matang dengan:

```text
support ≈ 15.48
confidence ≈ 0.943
known variables = 3
```

Di bagian lain:

```text
support ≈ 19.03
confidence ≈ 0.920
known variables = 4
```

Jadi neutral regime memang bekerja pada **saturated knowledge**, bukan pada cold-start state.

---

# 14. Exploration Regime

Exploration rate turun menjadi 23.2%.

Trace awal menunjukkan:

```text
cycle 1
action = drink
mode = explore
selected_novelty = 1.0
max_novelty = 1.0
saturated = false
```

Pada awal run semua action memang memiliki evidence 0 dan novelty 1.0. Ini adalah kondisi exploration yang valid.

Ketika evidence bertambah, novelty turun dan akhirnya mencapai saturation.

---

# 15. Context Behavior

V0.5.3 hanya mengunjungi 4 contexts:

```text
(LOW,LOW,HIGH,HIGH) : 493
(HIGH,LOW,HIGH,HIGH) : 3
(LOW,LOW,HIGH,LOW)  : 3
(HIGH,HIGH,HIGH,HIGH): 1
```

Context changes:

```text
4
```

dengan self-loop utama:

```text
(LOW,LOW,HIGH,HIGH)
→
(LOW,LOW,HIGH,HIGH)
= 492
```

Dengan demikian, seperti V0.5.2, **context churn bukan penyebab pathology policy**.

---

# 16. Regime Quality

V0.5.3 mencatat:

```text
Mean exploration novelty : 0.4364
Max exploration novelty  : 1.0000
Min exploration novelty  : 0.250086

Mean neutral harm        : 0.0
Min neutral harm         : 0.0
```

Temuan penting:

### Exploration

Minimum exploration novelty:

$$  
0.250086  
$$

sangat dekat dengan threshold `0.25`.

Ini menunjukkan exploration berhenti tepat di sekitar boundary yang kita definisikan.

### Neutral

Mean harm:

$$  
0.0  
$$

Ini menunjukkan neutral regime hampir sepenuhnya memilih action zero-harm.

Itulah sumber neutral lock.

---

# 17. Comparison V0.5.1 → V0.5.3

|Metrik|V0.5.1|V0.5.2|V0.5.3|
|---|--:|--:|--:|
|Alive|✅|✅|✅|
|Cycles|500|500|500|
|LR cells|24|40|40|
|Explore|5|397|116|
|Exploit|495|103|34|
|Neutral|—|—|350|
|Sleep|409|98|40|
|Drink|12|104|361|
|Context changes|157|4|4|

V0.5.1 mengalami sleep lock, V0.5.2 mengalami exploration dominance, dan V0.5.3 menurunkan exploration tetapi menghasilkan drink dominance pada neutral regime.

---

# 18. Evaluasi Hipotesis V0.5.3

### Hipotesis 1

> Saturation threshold dapat menghentikan exploration ketika evidence sudah cukup matang.

**Didukung.**

Trace secara eksplisit menunjukkan `max_novelty ≤ 0.25` menghasilkan `saturated=true` dan mode `neutral`.

### Hipotesis 2

> Least-harm dapat memberikan fallback policy yang stabil setelah exploration saturated.

**Sebagian didukung.**

Mechanism berjalan dan tidak menyebabkan fallback/death. Tetapi result behavioral menunjukkan neutral lock: `drink` mendominasi 326/350 neutral decisions.

### Hipotesis 3

> Least-harm akan memilih action yang sesuai dengan kebutuhan state.

**Tidak didukung.**

Final thirst `0.0`, tetapi `drink` masih menjadi neutral action dominan.

---

# 19. Diagnosis

V0.5.3 membuktikan bahwa:

```text
Learning
    ✅

Exploration
    ✅

Saturation
    ✅

Least-harm calculation
    ✅

Neutral policy semantics
    ❌ incomplete
```

Masalah bukan pada perhitungan harm.

Masalahnya adalah objective:

$$  
\arg\min Harm  
$$

tidak membedakan dua kondisi berikut:

```text
drink:
    tidak merusak

idle:
    tidak merusak
```

tetapi tidak menjawab apakah `drink` **dibutuhkan**.

Dengan kata lain:

> **Zero harm ≠ optimal neutral behavior.**

---

# 20. Evolusi Policy

Eksperimen tiga versi menunjukkan progression yang sangat jelas:

```text
V0.5.1
no positive
    ↓
best known
    ↓
SLEEP LOCK
```

kemudian:

```text
V0.5.2
no positive
    ↓
novelty exploration
    ↓
EXPLORATION LOCK
```

kemudian:

```text
V0.5.3
no positive
+
saturated
    ↓
least harm
    ↓
ZERO-HARM / DRINK LOCK
```

Jadi setiap versi berhasil mengatasi regime sebelumnya, tetapi mengungkap objective deficiency berikutnya.

---

# 21. Kesimpulan

V0.5.3 **berhasil secara mekanis dan eksperimental pada dua hal utama**:

1. Exploration sekarang memiliki stopping condition yang terukur.
    
2. Neutral regime benar-benar menggunakan predicted harm, bukan sekadar tie-breaking score.
    

Namun V0.5.3 **belum merupakan policy final** karena neutral regime hanya meminimalkan harm.

Hasil akhir:

```text
Alive          : True
Explore        : 23.2%
Exploit        : 6.8%
Neutral        : 70.0%
Drink          : 72.2% dari seluruh action
```

Temuan paling penting:

$$
\boxed{  
\text{least harm}  
\neq  
\text{least unnecessary action}  
}  
$$

Oleh karena itu, perubahan berikutnya tidak seharusnya menyentuh `saturation.py`. Saturation sudah berfungsi. Problem berikutnya berada pada **definisi neutral objective**.

### Status V0.5.3

```text
✅ Survival
✅ LR
✅ Scoring
✅ Exploration
✅ Saturation
✅ Least-harm calculation

⚠️ Neutral selection
   → drink lock
```

V0.5.3 karena itu sebaiknya dibekukan sebagai **experimental baseline** untuk merumuskan komponen neutral policy pada versi berikutnya.