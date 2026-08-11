Self-supervised learning berbasis prediksi keadaan lingkungan berikutnya.

Alurnya:
State saat ini + Action
↓
Lingkungan
↓
State berikutnya
↓
Data pengalaman
↓
Training model
↓
World Model

Secara sederhana:
$$
(s_t, a_t) \rightarrow s_{t+1}  
$$
Model belajar memprediksi **keadaan lingkungan berikutnya** berdasarkan keadaan saat ini dan tindakan agen.

Model yang sudah dipelajari kemudian **disimpan**, sehingga pada siklus operasional berikutnya dapat **dimuat kembali dan diperbarui menggunakan pengalaman baru**.

**Intinya:** agen tidak membutuhkan label manusia; pengalaman interaksinya sendiri menjadi data pembelajaran.