# Tugas Watermarking Foto Wajah

**Muhammad Fariz Difaurrahman — 18224028**

---

## Spesifikasi Tugas

1. Menambahkan watermark pada foto wajah sendiri.
2. Watermark berupa citra biner.
3. Citra ber-watermark dikompresi menggunakan kompresi JPEG.
4. Evaluasi kinerja watermark dilakukan dengan mengubah quality factor (QF) ke beberapa nilai dan menentukan QF yang membuat watermark tidak dapat diekstrak.

## Pendekatan

Watermarking dilakukan di domain frekuensi menggunakan Discrete Cosine Transform (DCT) pada kanal Y (luminance) dari ruang warna YUV. Kanal U dan V dibiarkan tidak berubah sehingga citra tetap berwarna. Citra ber-watermark kemudian dikompresi JPEG dengan beberapa nilai QF, lalu watermark diekstrak kembali dan kemiripannya dengan watermark asli diukur menggunakan tiga metrik: Normalized Correlation (NC), Bit Error Rate (BER), dan Peak Signal-to-Noise Ratio (PSNR).

## Proses Kompresi JPEG

Untuk memahami mengapa watermark bertahan pada QF tinggi tetapi rusak pada QF rendah, perlu ditinjau tahapan kompresi JPEG. Kompresi JPEG terdiri dari tujuh tahapan yang dijalankan secara berurutan: color conversion, downsampling chroma, blocking, forward DCT, quantization, zig-zag scan, dan entropy coding. Tahap quantization adalah tahap yang menentukan tingkat kompresi (dan kerusakan watermark) karena di sinilah Quality Factor bekerja.

### Tahap 1 — Color Conversion

Citra RGB dikonversi ke ruang warna YCbCr yang memisahkan informasi kecerahan (Y) dari informasi warna (Cb, Cr). Pemisahan ini memanfaatkan fakta bahwa mata manusia lebih sensitif terhadap kecerahan dibanding warna.

![Color Conversion](readme-assets/01_color_conversion.png)

### Tahap 2 — Chroma Downsampling

Kanal Cb dan Cr diperkecil dengan faktor 2 di kedua sumbu (pola 4:2:0), sehingga ukuran datanya menjadi seperempat dari aslinya. Kanal Y tidak diubah agar detail kecerahan tetap utuh. Tahap ini sudah memberi penghematan ukuran file yang signifikan tanpa banyak kehilangan kualitas yang terlihat.

![Chroma Downsampling](readme-assets/02_downsampling.png)

### Tahap 3 — Blocking

Setiap kanal dipecah menjadi blok-blok 8×8 piksel. Semua tahap setelah ini bekerja per blok, tidak per piksel utuh. Skema watermarking yang digunakan dalam tugas ini juga menyisipkan watermark per blok 8×8 di kanal Y, sehingga ukuran blok JPEG dan ukuran blok watermark sengaja dibuat sama.

![Blocking](readme-assets/03_blocking.png)

### Tahap 4 — Forward DCT

Setiap blok 8×8 ditransformasikan dari domain spasial (nilai piksel) ke domain frekuensi menggunakan Discrete Cosine Transform. Hasilnya juga matriks 8×8, dengan koefisien di sudut kiri-atas mewakili komponen DC (rata-rata blok), koefisien di sekitarnya mewakili frekuensi rendah (perubahan halus), dan koefisien di sudut kanan-bawah mewakili frekuensi tinggi (detail tajam dan tepi).

![Forward DCT](readme-assets/04_dct.png)

### Tahap 5 — Quantization

Setiap koefisien DCT dibagi dengan nilai yang sesuai pada tabel quantization Q, lalu hasilnya dibulatkan ke integer. Tahap inilah yang membuang sebagian informasi dan tidak dapat dibalik. Quality Factor (QF) menentukan seberapa "kasar" tabel Q: QF tinggi menghasilkan nilai Q kecil sehingga divisi-nya ringan dan banyak koefisien tetap bertahan, sementara QF rendah menghasilkan nilai Q besar sehingga banyak koefisien dibulatkan menjadi nol. Inilah penyebab utama mengapa watermark rusak pada QF rendah: koefisien mid-frequency yang menjadi pembawa watermark ikut dibulatkan ke nol.

![Quantization](readme-assets/05_quantization.png)

### Tahap 6 — Zig-zag Scan

Matriks koefisien hasil quantization yang berukuran 8×8 dibaca dalam pola zig-zag mulai dari kiri-atas ke kanan-bawah, sehingga menjadi urutan satu dimensi berisi 64 nilai. Urutan ini disusun sedemikian rupa agar koefisien frekuensi rendah berada di awal dan koefisien frekuensi tinggi (yang banyak bernilai nol setelah quantization) berada di akhir. Akibatnya, urutan biasanya diakhiri oleh deretan panjang nilai nol yang dapat dipadatkan dengan penanda End-of-Block.

![Zigzag Scan](readme-assets/06_zigzag.png)

### Tahap 7 — Entropy Coding

Urutan angka dari tahap zig-zag dikompresi lagi menggunakan Huffman coding. Nilai yang sering muncul (seperti 0 dan ±1) diberi kode bit yang pendek, sedangkan nilai yang jarang muncul diberi kode bit yang panjang. Tahap ini bersifat lossless, jadi tidak menambah kerusakan watermark.

![Entropy Coding](readme-assets/07_entropy.png)

Dari tujuh tahap di atas, hanya tahap 5 (quantization) yang sifatnya lossy alias merusak informasi. Tahap inilah yang menentukan tingkat kerusakan watermark. Saat QF turun, lebih banyak koefisien DCT dibulatkan menjadi nol, termasuk pasangan koefisien mid-frequency `[0,1]` dan `[1,0]` yang menjadi pembawa watermark dalam skema yang digunakan. Ketika kedua koefisien ini sama-sama menjadi nol, perbandingan yang menjadi dasar ekstraksi tidak dapat lagi menghasilkan jawaban yang benar, dan watermark menjadi rusak.

## Catatan Penggunaan AI

Sebagai dasar implementasi, saya menggunakan repository publik [arooshiverma/Image-Watermarking-using-DCT](https://github.com/arooshiverma/Image-Watermarking-using-DCT) yang menyediakan kerangka DCT watermarking dengan pemilihan blok pseudorandom. Repository tersebut hanya menguji ketahanan watermark terhadap serangan geometric (scaling, cutting) dan signal (filter, noise), tanpa pengujian kompresi JPEG yang menjadi fokus tugas ini.

Untuk menyesuaikan dengan kebutuhan tugas, saya menggunakan bantuan AI (Claude) untuk melakukan modifikasi berikut pada kode:

- Mengubah posisi penyisipan watermark dari koefisien DC `[0,0]` ke pasangan koefisien mid-frequency `[0,1]` dan `[1,0]`. Pada percobaan awal, penyisipan di `[0,0]` menghasilkan watermark yang tidak dapat diekstrak sekalipun pada QF tinggi karena koefisien DC terlalu sensitif terhadap quantization JPEG.
- Mengganti metode embedding dari odd/even rounding (versi asli) ke differential alpha-based embedding agar lebih tahan terhadap kompresi.
- Memproses citra di kanal Y dari ruang warna YUV sehingga output tetap berwarna, bukan grayscale seperti versi asli.
- Menambahkan loop pengujian quality factor JPEG dengan perhitungan Bit Error Rate (BER) yang tidak ada di repository aslinya.
- Menambahkan modul visualisasi grafik NC dan BER terhadap QF serta grid analisis visual per QF.

Logika algoritma DCT, pembagian blok 8×8, dan pemilihan blok pseudorandom dengan kunci tetap mengacu pada repository sumber. Saya memahami setiap baris kode yang digunakan dan menjalankannya secara mandiri di Visual Studio Code untuk memperoleh hasil yang dilaporkan di sini.

## Input

Foto wajah disimpan sebagai `image1.jpg` dan watermark biner disimpan sebagai `watermark2.jpg`.

![Input](readme-assets/00_input.png)

## Implementasi

Implementasi ditulis dalam Python dan dijalankan di Visual Studio Code dengan library OpenCV, NumPy, dan Matplotlib. Seluruh kode disusun dalam satu file `code.py`.

### Tahap embedding

1. Foto wajah dibaca sebagai citra BGR berwarna lalu diubah ukurannya menjadi 1000×1000 piksel agar pembagian blok 8×8 menjadi seragam.
2. Citra dikonversi dari BGR ke ruang warna YUV. Kanal Y (luminance) dipisahkan untuk diproses, sedangkan kanal U dan V disimpan untuk digabung kembali setelah embedding selesai.
3. Watermark di-resize menjadi 64×64 piksel kemudian dibinerisasi dengan threshold 127 sehingga setiap piksel hanya bernilai 0 (hitam) atau 1 (putih).
4. Kanal Y dibagi menjadi blok-blok 8×8 dengan margin tepi 50 piksel yang dilewati untuk menghindari distorsi pada area tepi.
5. Sebanyak 4096 blok (sesuai jumlah piksel watermark 64×64) dipilih secara acak menggunakan pseudorandom generator dengan seed = 50 sebagai kunci.
6. Setiap blok terpilih ditransformasikan ke domain frekuensi dengan DCT. Penyisipan bit dilakukan dengan memodifikasi pasangan koefisien mid-frequency, yaitu `[0,1]` dan `[1,0]`, menggunakan strength factor alpha = 15. Untuk bit 1, `[0,1]` dinaikkan dan `[1,0]` diturunkan; untuk bit 0, sebaliknya.
7. Blok dikembalikan ke domain spasial dengan IDCT, kanal Y yang telah dimodifikasi digabung kembali dengan kanal U dan V, lalu YUV dikonversi balik ke BGR sebagai citra berwarna.

### Tahap ekstraksi

Menggunakan metode informed dengan kunci yang sama (seed = 50):

1. Citra ber-watermark dikonversi ke YUV dan kanal Y diambil sebagai sumber ekstraksi.
2. Urutan blok yang dipilih saat embedding direproduksi secara identik dengan menggunakan seed yang sama.
3. Pada setiap blok, DCT dihitung lalu koefisien `[0,1]` dibandingkan dengan `[1,0]`. Apabila `[0,1] > [1,0]` maka piksel watermark bernilai 1 (putih), apabila sebaliknya maka bernilai 0 (hitam).

Pemilihan koefisien mid-frequency dilakukan karena pada percobaan awal penggunaan koefisien DC menghasilkan watermark yang tidak dapat dipulihkan setelah kompresi JPEG sekalipun pada QF tinggi. Koefisien mid-frequency cenderung lebih stabil terhadap quantization JPEG sehingga memberikan trade-off yang baik antara imperceptibility dan robustness.

## Kode Program

Konfigurasi awal dan parameter watermarking:

```python
import os, math, random
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

img_name = "image1.jpg"
wm_name = "watermark2.jpg"
KEY = 50           # seed pseudorandom (kunci watermark)
BS = 8             # block size 8x8
W1, W2 = 64, 64    # ukuran watermark
ALPHA = 15.0       # strength factor
B_CUT = 50         # margin tepi
IMG_SIZE = 1000
COEF_A = (0, 1)    # koefisien mid-frequency pertama
COEF_B = (1, 0)    # koefisien mid-frequency kedua
QUALITY_FACTORS = [90, 70, 50, 30, 10, 5, 1]
NC_THRESHOLD = 0.5
BER_THRESHOLD = 0.3
```

Preprocessing citra wajah (BGR berwarna) dan watermark sebelum embedding:

```python
img_bgr = cv.imread(img_name)  # baca berwarna (BGR)
if img_bgr.shape[:2] != (IMG_SIZE, IMG_SIZE):
    img_bgr = cv.resize(img_bgr, (IMG_SIZE, IMG_SIZE))

wm = cv.imread(wm_name, 0)
wm = cv.resize(wm, (W2, W1), interpolation=cv.INTER_NEAREST)
_, wm = cv.threshold(wm, 127, 255, cv.THRESH_BINARY)
```

Fungsi pemilihan blok pseudorandom dengan seed sebagai kunci. Fungsi yang sama dipanggil saat embedding maupun ekstraksi sehingga urutan blok yang dipilih identik.

```python
def _select_blocks(total_blocks, needed, seed):
    random.seed(seed)
    used = set()
    selected = []
    while len(selected) < needed:
        x = random.randint(0, total_blocks - 1)
        if x in used:
            continue
        used.add(x)
        selected.append(x)
    return selected
```

Fungsi embedding watermark. Citra BGR dikonversi ke YUV, watermark disisipkan pada kanal Y, kemudian dikonversi balik ke BGR berwarna.

```python
def watermark_image(img_bgr, wm):
    # BGR -> YUV, pisahkan kanal Y (luminance)
    yuv = cv.cvtColor(img_bgr, cv.COLOR_BGR2YUV)
    y, u, v = cv.split(yuv)

    h, w = y.shape
    area_h = h - B_CUT * 2
    area_w = w - B_CUT * 2
    n_blocks_w = area_w // BS
    total_blocks = (area_h // BS) * n_blocks_w
    needed = W1 * W2

    y_f = y.astype(np.float32)
    final = y_f.copy()
    wm_bin = (wm >= 127).astype(np.uint8)
    selected = _select_blocks(total_blocks, needed, KEY)

    for bit_idx in range(needed):
        block_idx = selected[bit_idx]
        bi = block_idx // n_blocks_w
        bj = block_idx % n_blocks_w
        ind_i = bi * BS + B_CUT
        ind_j = bj * BS + B_CUT

        block = final[ind_i:ind_i+BS, ind_j:ind_j+BS]
        dct_block = cv.dct(block)

        wm_bit = wm_bin[bit_idx // W2, bit_idx % W2]
        if wm_bit == 1:
            dct_block[COEF_A] += ALPHA
            dct_block[COEF_B] -= ALPHA
        else:
            dct_block[COEF_A] -= ALPHA
            dct_block[COEF_B] += ALPHA

        final[ind_i:ind_i+BS, ind_j:ind_j+BS] = cv.idct(dct_block)

    # Gabungkan kembali Y' + U + V, lalu YUV -> BGR
    y_watermarked = np.clip(final, 0, 255).astype(np.uint8)
    yuv_watermarked = cv.merge((y_watermarked, u, v))
    return cv.cvtColor(yuv_watermarked, cv.COLOR_YUV2BGR)
```

Fungsi ekstraksi watermark. Ambil kanal Y dari citra ber-watermark lalu bandingkan koefisien `[0,1]` dan `[1,0]` di setiap blok terpilih.

```python
def extract_watermark(img_bgr, ext_name):
    h, w = img_bgr.shape[:2]
    if h != IMG_SIZE or w != IMG_SIZE:
        img_bgr = cv.resize(img_bgr, (IMG_SIZE, IMG_SIZE))

    # Ambil kanal Y, lakukan DCT pada blok yang sama
    yuv = cv.cvtColor(img_bgr, cv.COLOR_BGR2YUV)
    y, _, _ = cv.split(yuv)

    area_h = IMG_SIZE - B_CUT * 2
    area_w = IMG_SIZE - B_CUT * 2
    n_blocks_w = area_w // BS
    total_blocks = (area_h // BS) * n_blocks_w
    needed = W1 * W2

    y_f = y.astype(np.float32)
    selected = _select_blocks(total_blocks, needed, KEY)
    wm_extracted = np.zeros((W1, W2), dtype=np.uint8)

    for bit_idx in range(needed):
        block_idx = selected[bit_idx]
        bi = block_idx // n_blocks_w
        bj = block_idx % n_blocks_w
        ind_i = bi * BS + B_CUT
        ind_j = bj * BS + B_CUT

        block = y_f[ind_i:ind_i+BS, ind_j:ind_j+BS]
        dct_block = cv.dct(block)

        if dct_block[COEF_A] > dct_block[COEF_B]:
            wm_extracted[bit_idx // W2, bit_idx % W2] = 255
        else:
            wm_extracted[bit_idx // W2, bit_idx % W2] = 0

    return wm_extracted
```

Tiga fungsi metrik kuantitatif:

```python
def psnr(img1, img2):
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return 100.0
    return 20 * math.log10(255.0 / math.sqrt(mse))

def NCC(wm1, wm2):
    wm1_bin = (wm1 >= 127).astype(np.float64)
    wm2_bin = (wm2 >= 127).astype(np.float64)
    num = np.sum(wm1_bin * wm2_bin)
    den = np.sqrt(np.sum(wm1_bin ** 2) * np.sum(wm2_bin ** 2))
    return float(num / den) if den != 0 else 0.0

def BER(wm1, wm2):
    wm1_bin = (wm1 >= 127).astype(np.uint8)
    wm2_bin = (wm2 >= 127).astype(np.uint8)
    return float(np.sum(wm1_bin != wm2_bin)) / wm1_bin.size
```

Loop evaluasi terhadap beberapa nilai QF JPEG. Citra ber-watermark disimpan dengan parameter `cv.IMWRITE_JPEG_QUALITY`, lalu dibaca kembali dan watermark-nya diekstrak untuk dihitung metriknya.

```python
for qf in QUALITY_FACTORS:
    compressed_path = f"compressed/compressed_qf_{qf}.jpg"
    cv.imwrite(compressed_path, watermarked_bgr,
               [int(cv.IMWRITE_JPEG_QUALITY), qf])

    img_compressed = cv.imread(compressed_path)  # BGR berwarna
    wm_extracted = extract_watermark(img_compressed,
                                     f"compressed/extracted_qf_{qf}.jpg")

    nc = NCC(wm_original, wm_extracted)
    ber = BER(wm_original, wm_extracted)
    psnr_c = psnr(watermarked_bgr, img_compressed)
    status = "VALID" if (nc >= NC_THRESHOLD and ber <= BER_THRESHOLD) else "RUSAK"
```

## Evaluasi Metrik

Tiga metrik kuantitatif digunakan untuk menilai kualitas watermark hasil ekstraksi pada tiap QF:

- **Normalized Correlation (NC)** mengukur kemiripan pola antara watermark asli dengan hasil ekstraksi dengan rentang nilai 0 sampai 1.
- **Bit Error Rate (BER)** menghitung proporsi bit watermark yang nilainya berbeda dari aslinya.
- **Peak Signal-to-Noise Ratio (PSNR)** mengukur kekuatan sinyal citra asli terhadap derau yang diakibatkan kompresi dalam satuan desibel.

Threshold yang digunakan untuk menyatakan watermark masih valid adalah NC ≥ 0,5 dan BER ≤ 0,3.

Pengujian dilakukan pada QF 90, 70, 50, 30, 10, 5, dan 1. Hasil pengujian disajikan pada tabel berikut.

| QF | Ukuran (KB) | NC    | BER   | PSNR (dB) | Status |
|----|-------------|-------|-------|-----------|--------|
| 90 | 177.82      | 0.682 | 0.192 | 41.67     | VALID  |
| 70 | 96.45       | 0.673 | 0.200 | 37.63     | VALID  |
| 50 | 71.29       | 0.652 | 0.213 | 35.66     | VALID  |
| 30 | 52.66       | 0.586 | 0.253 | 33.68     | VALID  |
| 10 | 29.52       | 0.345 | 0.370 | 28.98     | RUSAK  |
| 5  | 22.25       | 0.303 | 0.362 | 25.15     | RUSAK  |
| 1  | 18.61       | 0.274 | 0.349 | 22.10     | RUSAK  |

Grafik nilai NC dan BER terhadap QF disajikan pada gambar berikut.

![Grafik Kinerja](readme-assets/08_grafik.png)

## Analisis Hasil

Pada QF 90, 70, 50, dan 30, watermark masih dapat diekstrak dengan baik karena nilai NC tetap di atas 0,5 dan BER di bawah 0,3. Bentuk watermark berupa logo burung Twitter masih dapat dikenali secara visual pada keempat QF tersebut, meskipun mulai muncul gangguan pada area tepi seiring turunnya QF.

Pada QF 10, nilai NC turun menjadi 0,345 yang sudah di bawah threshold dan BER mencapai 0,370 yang sudah melampaui batas 0,3. Pada titik ini sebagian besar bit watermark sudah salah dan logo burung tidak lagi dapat dikenali secara visual, sehingga watermark dianggap rusak. Pada QF ini citra wajah juga mulai memperlihatkan blocking artifact yang khas dari kompresi JPEG agresif.

Pada QF 5 dan 1, baik NC maupun BER tetap melewati threshold dan pola yang muncul pada hasil ekstraksi sudah berupa noise acak tanpa bentuk yang dikenali. Citra wajah pada QF 1 sudah mengalami posterisasi dengan blocking yang sangat jelas.

Dengan demikian, batas QF yang masih aman untuk skema watermarking ini adalah QF 30 ke atas. Watermark gagal diekstrak ketika QF turun ke 10 atau di bawahnya.

## Visualisasi per QF

Citra ber-watermark pada setiap QF serta hasil ekstraksi watermark-nya disajikan pada dua gambar berikut. Gambar pertama untuk QF yang masih valid (QF 90, 70, 50, 30), gambar kedua untuk QF yang menyebabkan watermark rusak (QF 10, 5, 1).

![Visualisasi QF Valid](readme-assets/09_visual_valid.png)

*Visualisasi QF yang masih valid: 90, 70, 50, dan 30.*

![Visualisasi QF Rusak](readme-assets/10_visual_rusak.png)

*Visualisasi QF yang menyebabkan watermark rusak: 10, 5, dan 1.*

## Kesimpulan

Skema watermarking berbasis DCT yang diimplementasikan tahan terhadap kompresi JPEG hingga QF 30. Pada QF 10 atau lebih rendah, watermark tidak lagi dapat diekstrak karena NC turun di bawah 0,5 dan BER melampaui 0,3. Hal ini sesuai dengan karakteristik kompresi JPEG yang memperbesar kuantisasi koefisien DCT ketika QF turun, sehingga modifikasi halus pada koefisien mid-frequency yang menjadi pembawa watermark menjadi terlalu kecil untuk dapat diinterpretasikan kembali.

## Cara Menjalankan

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Letakkan image1.jpg dan watermark2.jpg di folder yang sama dengan code.py

# 3. Jalankan
python code.py
```

Output akan tersimpan di folder `compressed/` dan `reports/`.
