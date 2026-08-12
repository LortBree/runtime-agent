# LAPORAN EKSPERIMEN ENTITY CORE — V0.5.2

## 1. Ringkasan Eksekutif

V0.5.2 mengubah **selection policy** Layer 3 tanpa mengubah mekanisme scoring utama maupun Knowledge Layer. Perubahan inti adalah: ketika tidak ada action dengan positive current-context score, Decision tidak lagi memilih known action dengan score tertinggi yang bisa bernilai `0`; Decision mendelegasikan pemilihan ke `ExplorationPolicy` berbasis novelty/evidence maturity.

Hasil 500-cycle menunjukkan perubahan tersebut **berhasil menghilangkan sleep lock V0.5.1**, dengan survival tetap tercapai selama 500 cycle. Namun, perubahan tersebut menghasilkan kondisi baru berupa **exploration dominance**: 397 dari 500 cycle berada dalam mode exploration, atau 79,4%. Action distribution menjadi hampir merata di lima action.

Kesimpulan utama:

> **V0.5.2 berhasil memperbaiki patologis zero-score/sleep lock V0.5.1, tetapi belum menghasilkan policy yang balanced karena exploration tidak memiliki stopping condition ketika knowledge sudah matang.**

---

# 2. Tujuan V0.5.2

V0.5.1 menunjukkan pola dominan `sleep`:

```text
sleep = 409 / 500
```

dan mayoritas keputusan `sleep` tersebut terjadi dengan score `0.0`. V0.5.2 dirancang untuk menguji hipotesis:

> Ketika tidak ada positive current-context utility, agent sebaiknya melakukan exploration berdasarkan novelty/evidence maturity daripada terus mengeksploitasi known action dengan score nol.

Scoring action V0.5.1 dipertahankan. Yang diubah adalah perilaku **post-scoring selection**.

---

# 3. Perubahan Arsitektur

Struktur Layer 3 untuk V0.5.2:

```text
EntityCore
    ↓
DecisionEngine
    ├── score action
    ├── exploit positive score
    └── ExplorationPolicy
            ↓
       novelty-based selection
```

`EntityCore` tetap menjadi thin orchestrator; ia tetap melakukan observe → retrieve knowledge → decision → execute → experience → update knowledge. Tidak diperlukan perubahan arsitektural pada orchestrator.

`decision.py` V0.5.2 mempertahankan scoring relation:

$$
contribution =  
ContextWeight  
\times  
Desirability  
\times  
Confidence  
$$

dan total score action merupakan agregasi kontribusi relation. Sistem magnitude/desirability dan context weighting V0.5.1 tetap dipertahankan.

Perubahan hanya terjadi pada selection branch:

```text
V0.5.1

positive score
    → exploit

no positive
    → unknown action
    → atau best known score
    → atau fallback
```

menjadi:

```text
V0.5.2

positive score
    → exploit

no positive
    → ExplorationPolicy
```

---

# 4. Exploration Policy

ExplorationPolicy menggunakan evidence maturity sebagai basis novelty:

$$
Novelty(a)=  
\frac{k}{E(a)+k}  
$$

dengan:

- (E(a)) = current-context evidence;
    
- (k=5.0) pada implementasi eksperimen.
    

Karakteristiknya:

```text
evidence = 0   → novelty = 1.000
evidence = 1   → novelty ≈ 0.833
evidence = 5   → novelty = 0.500
evidence = 10  → novelty ≈ 0.333
evidence = 20  → novelty = 0.200
```

Dengan demikian, action dengan evidence lebih sedikit menjadi kandidat exploration yang lebih menarik.

Unit test `exploration.py` berhasil:

```text
sleep   evidence=18.50 novelty=0.213
eat     evidence= 3.00 novelty=0.625
drink   evidence= 5.00 novelty=0.500
work    evidence=14.00 novelty=0.263

Selected: eat
PASS
```

Eksperimen juga memverifikasi bahwa action dengan positive score tetap masuk exploit sementara action pada no-positive regime masuk exploration.

---

# 5. Konfigurasi Eksperimen

Eksperimen V0.5.2 menggunakan:

|Parameter|Nilai|
|---|---|
|Total cycles|500|
|Seed|42|
|Initial hunger|60.0|
|Initial thirst|60.0|
|Initial energy|60.0|
|Initial curiosity|50.0|
|Environment|sama dengan baseline V0.5.1|
|Knowledge mechanism|sama dengan baseline|
|Scoring mechanism|sama dengan baseline|

Trace lengkap disimpan dalam `baseline_052_trace.json`, sedangkan summary disimpan dalam `baseline_052_summary.txt`. Total trace terdiri dari 500 records.

---

# 6. Hasil Survival

V0.5.2 berhasil bertahan sepanjang eksperimen:

```text
Alive          : True
Total cycles   : 500
Simulated days : 101
LR cells       : 40
```

Tidak terjadi fallback death maupun early termination.

---

# 7. Final State

State akhir:

```text
Hunger       : 2.0
Thirst       : 2.5
Energy       : 54.0
Curiosity    : 99.5
```

Dibandingkan baseline V0.5.1, state akhir V0.5.2 menunjukkan karakter yang jauh lebih exploration-heavy. Hunger dan thirst terdorong sangat rendah, sementara curiosity meningkat hampir ke batas atas.

Hal tersebut merupakan konsekuensi behavioral yang perlu diperhatikan; survival tercapai, tetapi distribusi state tidak otomatis menunjukkan homeostasis yang lebih baik.

---

# 8. Decision Statistics

V0.5.2 menghasilkan:

```text
Explore   : 397
Exploit   : 103
Fallback  : 0
```

Dengan demikian:

$$ 
P(Explore)=\frac{397}{500}=79.4%  
$$

dan:

$$ 
P(Exploit)=\frac{103}{500}=20.6%  
$$

Tidak ada fallback.

Ini merupakan kebalikan besar dari baseline V0.5.1, yang hampir sepenuhnya exploitation.

---

# 9. Action Distribution

V0.5.2 menghasilkan distribusi:

| Action | Count | Persentase |
| ------ | ----: | ---------: |
| eat    |   101 |      20.2% |
| drink  |   104 |      20.8% |
| sleep  |    98 |      19.6% |
| work   |    98 |      19.6% |
| idle   |    99 |      19.8% |

Distribusi menjadi sangat dekat dengan uniform.

Ini menunjukkan bahwa V0.5.2 **berhasil menghilangkan sleep dominance**, tetapi juga menunjukkan bahwa policy exploration mulai mendominasi behavior.

Uniformity ini sebaiknya tidak ditafsirkan sebagai bukti equilibrium optimal. Trace lebih konsisten dengan interpretasi bahwa agent terus melakukan novelty-based exploration karena tidak ada positive score.

---

# 10. Score Regime

Summary menunjukkan:

```text
Positive : 103
Zero     : 0
Negative : 0
```

Interpretasinya harus hati-hati.

Nilai `score=0` dan negatif tidak muncul sebagai score final decision karena pada kondisi tersebut V0.5.2 mengembalikan:

```text
score = None
mode  = explore
```

bukan memilih zero/negative action sebagai exploit.

Karena itu, metric yang lebih tepat adalah:

```text
Positive exploitation  : 103
No-positive exploration: 397
Fallback               : 0
```

bukan membandingkan positive/zero/negative sebagai tiga kategori yang saling eksklusif.

---

# 11. Bukti Langsung Perubahan Policy

Pada awal run, ketika semua relation belum tersedia, Decision masuk exploration.

Cycle 1:

```text
action  = drink
mode    = explore
reason  = no positive current-context score;
          selected by evidence novelty
```

Semua action masih memiliki evidence 0.

Setelah execution, environment menghasilkan real transition `thirst: 60 → 30`, dan LR belajar `DEC_LARGE` untuk thirst serta `NONE` pada variable lainnya.

Pada cycle 3, relation drink sudah menghasilkan positive score:

```text
drink score = 1.3333
mode = exploit
```

Ini membuktikan bahwa V0.5.2 **tidak menghilangkan exploitation**; ia hanya menggunakan exploration saat positive utility tidak tersedia.

---

# 12. Exploration Saturation

Masalah utama V0.5.2 muncul setelah knowledge menjadi matang.

Contoh cycle 173:

```text
state:
hunger   = 2.0
thirst   = 2.5
energy   = 65.5
curiosity= 99.5

action = work
mode   = explore
```

Tetapi evidence `work` sudah sangat matang:

```text
support ≈ 16.13
confidence ≈ 0.945
label = should
```

untuk sebagian besar variable.

Dengan kata lain, exploration masih terjadi walaupun action tersebut **bukan lagi knowledge frontier**.

---

# 13. Evidence Maturity Menjelang Akhir

Pada bagian akhir trace, evidence sudah mendekati saturasi.

Contoh cycle 486:

```text
work
mode = explore
```

sementara relation menunjukkan:

```text
support ≈ 19.84
confidence ≈ 0.954
label = should
```

untuk beberapa variable.

State saat itu:

```text
hunger   = 2.0
thirst   = 2.5
energy   = 100
curiosity= 97.5
```

Hal ini memberikan bukti bahwa **novelty-based exploration tidak memiliki stopping condition**.

Selama:

$$
Score_{\max}\le0  
$$

Decision terus masuk exploration, walaupun:

$$  
E(a)\approx20  
$$

dan confidence sudah mendekati 0.95.

---

# 14. Context Behavior

V0.5.2 hanya menggunakan 4 contexts:

```text
(LOW,LOW,HIGH,HIGH) : 493
(HIGH,LOW,HIGH,HIGH) : 3
(LOW,LOW,HIGH,LOW)  : 3
(HIGH,HIGH,HIGH,HIGH): 1
```

Total context changes hanya:

```text
4 / 500 = 0.8%
```

Context utama juga melakukan self-loop:

```text
(LOW,LOW,HIGH,HIGH)
→
(LOW,LOW,HIGH,HIGH)
= 492 kali
```

Dengan demikian, **context churn bukan penyebab exploration dominance**.

---

# 15. Evidence Maturity per Action

Summary menunjukkan evidence selected-action cukup matang secara keseluruhan:

|Action|Uses|Mean support|Mean confidence|
|---|--:|--:|--:|
|eat|98|15.755|0.915|
|drink|100|15.357|0.908|
|sleep|97|15.079|0.881|
|work|97|15.286|0.912|
|idle|98|16.148|0.935|

Ini adalah bukti kuat bahwa exploration dominance **bukan akibat kurangnya learning**.

Sebaliknya, agent terus mengeksplorasi ketika knowledge sudah relatif matang.

---

# 16. Interpretasi Sistem

V0.5.2 berhasil mengubah regime:

```text
V0.5.1
non-positive
    ↓
best known
    ↓
sleep lock
```

menjadi:

```text
V0.5.2
non-positive
    ↓
novelty exploration
    ↓
action diversification
```

Perubahan tersebut berhasil mengurangi sleep dominance, tetapi memperkenalkan regime baru:

```text
knowledge mature
        +
no positive utility
        ↓
exploration tetap berjalan
        ↓
action distribution mendekati uniform
```

Jadi masalah policy tidak hilang sepenuhnya; **lokasinya berpindah dari exploitation lock ke exploration saturation**.

---

# 17. Perbandingan V0.5.1 vs V0.5.2

|Metrik|V0.5.1|V0.5.2|
|---|--:|--:|
|Alive|True|True|
|Cycles|500|500|
|LR cells|24|40|
|Explore|5|397|
|Exploit|495|103|
|Fallback|0|0|
|Sleep|409|98|
|Eat|11|101|
|Drink|12|104|
|Work|67|98|
|Idle|1|99|
|Unique contexts|5|4|
|Context changes|157|4|

V0.5.2 memperluas action diversity dan knowledge coverage, tetapi juga secara dramatis meningkatkan exploration.

---

# 18. Evaluasi Hipotesis

### Hipotesis V0.5.2

> Ketika tidak ada positive utility, evidence-based exploration akan mengurangi zero-score action lock.

**Hasil: didukung.**

Evidence:

- sleep turun dari 409 menjadi 98;
    
- exploration meningkat dari 5 menjadi 397;
    
- action distribution menjadi jauh lebih beragam;
    
- survival tetap 500 cycle.
    

### Hipotesis implisit

> Novelty-based exploration akan secara alami berhenti ketika knowledge sudah matang.

**Hasil: tidak didukung.**

Trace menunjukkan exploration tetap terjadi ketika support mendekati 16–20 dan confidence mendekati 0.95.

---

# 19. Kelemahan V0.5.2

V0.5.2 memiliki tiga keterbatasan utama.

**Pertama, tidak ada exploration stopping condition.**

Selama `max score <= 0`, exploration terus dipanggil.

**Kedua, novelty masih dipakai walaupun evidence sudah mature.**

Evidence `~20` masih menghasilkan novelty positif, sehingga action tetap eligible untuk exploration.

**Ketiga, exploration tidak mempertimbangkan state quality secara langsung.**

Akibatnya agent bisa terus melakukan exploration saat hunger/thirst sangat rendah dan curiosity sudah sangat tinggi, seperti state akhir `2.0 / 2.5 / 54.0 / 99.5`.

---

# 20. Kesimpulan

**V0.5.2 adalah eksperimen yang berhasil secara diagnosis, tetapi belum merupakan policy final.**

Ia membuktikan:

$$
\boxed{  
\text{no-positive}  
\rightarrow  
\text{novelty exploration}  
}  
$$

secara efektif mengatasi sleep lock V0.5.1.

Namun eksperimen juga membuktikan:

$$
\boxed{  
\text{no-positive}  
\rightarrow  
\text{explore forever}  
}  
$$

adalah terlalu agresif.

Dengan demikian, V0.5.2 sebaiknya dibekukan sebagai **experimental baseline**, dan temuan utamanya adalah:

> **Exploration membutuhkan saturation/stopping condition.**

Target desain berikutnya secara logis bukan mengganti novelty formula, tetapi menambahkan regime ketiga:

$$
\boxed{  
\begin{aligned}  
Score_{\max} > 0  
&\Rightarrow Exploit\  
Score_{\max}\le0  
\land Novelty_{\max}>\tau  
&\Rightarrow Explore\  
Score_{\max}\le0  
\land Novelty_{\max}\le\tau  
&\Rightarrow Neutral/Fallback  
\end{aligned}  
}  
$$

Itulah hasil paling penting dari eksperimen V0.5.2 berdasarkan trace dan summary aktual.