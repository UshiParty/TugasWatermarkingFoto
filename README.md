# TugasWatermarkingFoto
Untuk memahami mengapa watermark bertahan pada QF tinggi tetapi rusak pada QF rendah, perlu ditinjau tahapan kompresi JPEG. Kompresi JPEG terdiri dari tujuh tahapan yang dijalankan secara berurutan: color conversion, downsampling chroma, blocking, forward DCT, quantization, zig-zag scan, dan entropy coding. Tahap quantization adalah tahap yang menentukan tingkat kompresi (dan kerusakan watermark) karena di sinilah Quality Factor bekerja.

Tahap 1: Color Conversion. Citra RGB dikonversi ke ruang warna YCbCr yang memisahkan informasi kecerahan (Y) dari informasi warna (Cb, Cr).
<img width="813" height="234" alt="image" src="https://github.com/user-attachments/assets/9aa47efe-f4a6-443e-8de4-4dea23abccd9" />


Tahap 2: Chroma Downsampling. Kanal Cb dan Cr diperkecil dengan faktor 2 di kedua sumbu (pola 4:2:0), sehingga ukuran datanya menjadi seperempat dari aslinya.
<img width="813" height="500" alt="image" src="https://github.com/user-attachments/assets/e2d0b64b-2d21-40cd-8915-e23f6e6523d4" />


Tahap 3: Blocking. Setiap kanal dipecah menjadi blok-blok 8×8 piksel. Skema watermarking yang digunakan dalam tugas ini juga menyisipkan watermark per blok 8×8 di kanal Y, sehingga ukuran blok JPEG dan ukuran blok watermark sengaja dibuat sama.
<img width="813" height="406" alt="image" src="https://github.com/user-attachments/assets/c327aa10-4dc1-42a9-988a-caf9627b741b" />


Tahap 4: Forward DCT. Setiap blok 8×8 ditransformasikan dari domain spasial (nilai piksel) ke domain frekuensi menggunakan Discrete Cosine Transform. koefisien di sudut kiri-atas mewakili komponen DC, koefisien di sekitarnya mewakili frekuensi rendah, dan koefisien di sudut kanan-bawah mewakili frekuensi tinggi.
<img width="813" height="273" alt="image" src="https://github.com/user-attachments/assets/57853bf4-227f-44f5-bf71-ae5379c3f630" />


Tahap 5: Quantization. Setiap koefisien DCT dibagi dengan nilai yang sesuai pada tabel quantization Q, lalu hasilnya dibulatkan ke integer. Quality Factor (QF) menentukan seberapa "kasar" tabel Q. Inilah penyebab utama watermark dapat rusak pada QF rendah.
<img width="813" height="531" alt="image" src="https://github.com/user-attachments/assets/5b2dd068-0fd4-46c4-8b97-67060889bfd8" />


Tahap 6: Zig-zag Scan. Matriks koefisien hasil quantization yang berukuran 8×8 dibaca dalam pola zig-zag mulai dari kiri-atas ke kanan-bawah, sehingga menjadi urutan satu dimensi berisi 64 nilai.
<img width="813" height="313" alt="image" src="https://github.com/user-attachments/assets/dc45ce6c-fbf9-4368-8462-48809b0edadc" />


Tahap 7: Entropy Coding. Urutan angka dari tahap zig-zag dikompresi lagi menggunakan Huffman coding.
<img width="813" height="438" alt="image" src="https://github.com/user-attachments/assets/0ea0998b-1e30-444b-9876-9845f506d4a4" />


Dari tujuh tahap di atas, hanya tahap 5 (quantization) yang sifatnya lossy alias merusak informasi. Tahap inilah yang menentukan tingkat kerusakan watermark. Saat QF turun, lebih banyak koefisien DCT dibulatkan menjadi nol, termasuk pasangan koefisien mid-frequency [0,1] dan [1,0] yang menjadi pembawa watermark dalam skema yang digunakan. Ketika kedua koefisien ini sama-sama menjadi nol, perbandingan yang menjadi dasar ekstraksi tidak dapat lagi menghasilkan jawaban yang benar, dan watermark menjadi rusak.

# Input
Foto wajah disimpan sebagai image1.jpg dan watermark biner disimpan sebagai watermark2.jpg.
<img width="719" height="359" alt="image" src="https://github.com/user-attachments/assets/29db9783-82cc-473d-9bdc-79dda7e5f37d" />
# Implementasi
Implementasi ditulis dalam Python dan dijalankan di Visual Studio Code dengan library OpenCV, NumPy, dan Matplotlib. Seluruh kode disusun dalam satu file code.py.
Tahap embedding dijalankan sebagai berikut:
1.	Foto wajah dibaca sebagai citra BGR berwarna lalu diubah ukurannya menjadi 1000×1000 piksel agar pembagian blok 8×8 menjadi seragam.
2.	Citra dikonversi dari BGR ke ruang warna YUV. Kanal Y (luminance) dipisahkan untuk diproses, sedangkan kanal U dan V disimpan untuk digabung kembali setelah embedding selesai.
3.	Watermark di-resize menjadi 64×64 piksel kemudian dibinerisasi dengan threshold 127 sehingga setiap piksel hanya bernilai 0 (hitam) atau 1 (putih).
4.	Kanal Y dibagi menjadi blok-blok 8×8 dengan margin tepi 50 piksel yang dilewati untuk menghindari distorsi pada area tepi.
5.	Sebanyak 4096 blok (sesuai jumlah piksel watermark 64×64) dipilih secara acak menggunakan pseudorandom generator dengan seed = 50 sebagai kunci.
6.	Setiap blok terpilih ditransformasikan ke domain frekuensi dengan DCT. Penyisipan bit dilakukan dengan memodifikasi pasangan koefisien mid-frequency, yaitu [0,1] dan [1,0], menggunakan strength factor alpha = 15. Untuk bit 1, [0,1] dinaikkan dan [1,0] diturunkan; untuk bit 0, sebaliknya.
7.	Blok dikembalikan ke domain spasial dengan IDCT, kanal Y yang telah dimodifikasi digabung kembali dengan kanal U dan V, lalu YUV dikonversi balik ke BGR sebagai citra berwarna.
Tahap ekstraksi menggunakan metode informed dengan kunci yang sama (seed = 50):
1.	Citra ber-watermark dikonversi ke YUV dan kanal Y diambil sebagai sumber ekstraksi.
2.	Urutan blok yang dipilih saat embedding direproduksi secara identik dengan menggunakan seed yang sama.
3.	Pada setiap blok, DCT dihitung lalu koefisien [0,1] dibandingkan dengan [1,0]. Apabila [0,1] > [1,0] maka piksel watermark bernilai 1 (putih), apabila sebaliknya maka bernilai 0 (hitam).
Pemilihan koefisien mid-frequency dilakukan karena pada percobaan awal penggunaan koefisien DC menghasilkan watermark yang tidak dapat dipulihkan setelah kompresi JPEG sekalipun pada QF tinggi. Koefisien mid-frequency cenderung lebih stabil terhadap quantization JPEG sehingga memberikan trade-off yang baik antara imperceptibility dan robustness.

