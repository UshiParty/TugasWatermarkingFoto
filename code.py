"""
DCT Watermarking dengan Evaluasi Kompresi JPEG
================================================
Berbasis pendekatan arooshiverma/Image-Watermarking-using-DCT
(DCT blok 8x8, pseudorandom block selection dengan key),
TAPI dengan modifikasi penting untuk ketahanan terhadap JPEG:

1. Sisipkan watermark di koefisien MID-FREQUENCY [0,1] dan [1,0]
   (bukan DC [0,0]), karena DC sangat sensitif terhadap quantization JPEG
2. Pakai differential embedding (alpha-based) — lebih robust daripada
   odd/even rounding seperti versi asli arooshiverma
3. Tambahkan loop QF + perhitungan BER, NC, PSNR
4. Tambahkan visualisasi grafik + analisis visual per QF

Cara pakai:
1. Letakkan foto wajah sebagai "image1.jpg" (akan di-resize otomatis ke 1000x1000)
2. Letakkan watermark sebagai "watermark2.jpg" (akan di-resize ke 64x64)
3. Jalankan: python code.py
"""

import os
import math
import random

import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

# ============================================================
# KONFIGURASI
# ============================================================
img_name = "image1.jpeg"
wm_name = "watermark2.png"
watermarked_img = "Watermarked_Image.png"
watermarked_extracted = "watermarked_extracted.png"

KEY = 50           # seed pseudorandom — "kunci" watermark
BS = 8             # block size 8x8
W1 = 64            # watermark width
W2 = 64            # watermark height
ALPHA = 15.0       # strength factor — makin besar = makin robust tapi PSNR turun
B_CUT = 50         # margin tepi yang di-skip
IMG_SIZE = 1000

# Koefisien mid-frequency yang dimodifikasi (pasangan)
COEF_A = (0, 1)
COEF_B = (1, 0)

QUALITY_FACTORS = [90, 70, 50, 30, 10, 5, 1]
NC_THRESHOLD = 0.5
BER_THRESHOLD = 0.3


# ============================================================
# METRIK
# ============================================================
def psnr(img1, img2):
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return 100.0
    return 20 * math.log10(255.0 / math.sqrt(mse))


def NCC(wm1, wm2):
    """Normalized Cross-Correlation antara dua watermark biner."""
    wm1_bin = (wm1 >= 127).astype(np.float64)
    wm2_bin = (wm2 >= 127).astype(np.float64)
    if wm1_bin.shape != wm2_bin.shape:
        wm2_bin = cv.resize(wm2_bin.astype(np.uint8) * 255,
                            (wm1_bin.shape[1], wm1_bin.shape[0]),
                            interpolation=cv.INTER_NEAREST)
        wm2_bin = (wm2_bin >= 127).astype(np.float64)
    num = np.sum(wm1_bin * wm2_bin)
    den = np.sqrt(np.sum(wm1_bin ** 2) * np.sum(wm2_bin ** 2))
    return float(num / den) if den != 0 else 0.0


def BER(wm1, wm2):
    """Bit Error Rate antara dua watermark biner."""
    wm1_bin = (wm1 >= 127).astype(np.uint8)
    wm2_bin = (wm2 >= 127).astype(np.uint8)
    if wm1_bin.shape != wm2_bin.shape:
        wm2_bin = cv.resize(wm2_bin, (wm1_bin.shape[1], wm1_bin.shape[0]),
                            interpolation=cv.INTER_NEAREST)
    return float(np.sum(wm1_bin != wm2_bin)) / wm1_bin.size


# ============================================================
# EMBEDDING
# ============================================================
def _select_blocks(total_blocks, needed, seed):
    """Pilih `needed` blok unik dari `total_blocks` pake seed (untuk konsistensi
    embed-extract).
    """
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


def watermark_image(img, wm):
    """Embed watermark wm (64x64 biner) ke img (1000x1000 grayscale)."""
    h, w = img.shape
    area_h = h - B_CUT * 2
    area_w = w - B_CUT * 2

    n_blocks_h = area_h // BS
    n_blocks_w = area_w // BS
    total_blocks = n_blocks_h * n_blocks_w
    needed = W1 * W2

    print(f"Image area embed: {area_h}x{area_w}, watermark: {W1}x{W2}")
    print(f"Blok tersedia: {total_blocks}, blok dibutuhkan: {needed}")

    if total_blocks < needed:
        raise ValueError("Watermark terlalu besar untuk image ini.")

    img_f = img.astype(np.float32)
    final = img_f.copy()

    wm_bin = (wm >= 127).astype(np.uint8)
    selected = _select_blocks(total_blocks, needed, KEY)

    for bit_idx in range(needed):
        block_idx = selected[bit_idx]
        bi = block_idx // n_blocks_w
        bj = block_idx % n_blocks_w
        ind_i = bi * BS + B_CUT
        ind_j = bj * BS + B_CUT

        block = final[ind_i:ind_i + BS, ind_j:ind_j + BS]
        dct_block = cv.dct(block)

        wm_bit = wm_bin[bit_idx // W2, bit_idx % W2]
        if wm_bit == 1:
            dct_block[COEF_A] += ALPHA
            dct_block[COEF_B] -= ALPHA
        else:
            dct_block[COEF_A] -= ALPHA
            dct_block[COEF_B] += ALPHA

        final[ind_i:ind_i + BS, ind_j:ind_j + BS] = cv.idct(dct_block)

    final_uint8 = np.clip(final, 0, 255).astype(np.uint8)
    print(f"PSNR (asli vs ber-watermark): {psnr(final_uint8, img):.2f} dB")

    cv.imwrite(watermarked_img, final_uint8)
    return final_uint8


# ============================================================
# EXTRACTING
# ============================================================
def extract_watermark(img, ext_name):
    """Ekstrak watermark 64x64 dari gambar ber-watermark.

    Butuh KEY yang sama dengan saat embedding (non-blind dalam arti butuh key).
    """
    h, w = img.shape
    if h != IMG_SIZE or w != IMG_SIZE:
        img = cv.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv.INTER_LINEAR)
        h, w = IMG_SIZE, IMG_SIZE

    area_h = h - B_CUT * 2
    area_w = w - B_CUT * 2
    n_blocks_h = area_h // BS
    n_blocks_w = area_w // BS
    total_blocks = n_blocks_h * n_blocks_w
    needed = W1 * W2

    img_f = img.astype(np.float32)
    selected = _select_blocks(total_blocks, needed, KEY)

    wm_extracted = np.zeros((W1, W2), dtype=np.uint8)

    for bit_idx in range(needed):
        block_idx = selected[bit_idx]
        bi = block_idx // n_blocks_w
        bj = block_idx % n_blocks_w
        ind_i = bi * BS + B_CUT
        ind_j = bj * BS + B_CUT

        block = img_f[ind_i:ind_i + BS, ind_j:ind_j + BS]
        dct_block = cv.dct(block)

        # Bandingkan koefisien [0,1] vs [1,0]
        # Embed bit=1: [0,1] += alpha, [1,0] -= alpha → [0,1] > [1,0]
        # Embed bit=0: [0,1] -= alpha, [1,0] += alpha → [0,1] < [1,0]
        if dct_block[COEF_A] > dct_block[COEF_B]:
            wm_extracted[bit_idx // W2, bit_idx % W2] = 255
        else:
            wm_extracted[bit_idx // W2, bit_idx % W2] = 0

    cv.imwrite(ext_name, wm_extracted)
    return wm_extracted


# ============================================================
# EVALUASI KOMPRESI JPEG
# ============================================================
def evaluate_jpeg_compression(watermarked, wm_original):
    os.makedirs("reports", exist_ok=True)
    os.makedirs("compressed", exist_ok=True)

    results = []
    compressed_images = []
    extracted_wms = []

    print("\n" + "=" * 75)
    print(" EVALUASI KETAHANAN DCT WATERMARKING TERHADAP KOMPRESI JPEG")
    print("=" * 75)
    print(f"{'QF':>4} | {'Size (KB)':>10} | {'NC':>6} | {'BER':>6} | "
          f"{'PSNR (dB)':>10} | Status")
    print("-" * 75)

    for qf in QUALITY_FACTORS:
        compressed_path = f"compressed/compressed_qf_{qf}.jpg"
        cv.imwrite(compressed_path, watermarked,
                   [int(cv.IMWRITE_JPEG_QUALITY), qf])

        img_compressed = cv.imread(compressed_path, 0)

        ext_path = f"compressed/extracted_qf_{qf}.jpg"
        wm_extracted = extract_watermark(img_compressed, ext_path)

        nc = NCC(wm_original, wm_extracted)
        ber = BER(wm_original, wm_extracted)
        psnr_c = psnr(watermarked, img_compressed)
        file_size = os.path.getsize(compressed_path) / 1024.0
        status = "VALID" if (nc >= NC_THRESHOLD and ber <= BER_THRESHOLD) else "RUSAK"

        print(f"{qf:>4} | {file_size:>10.2f} | {nc:>6.3f} | {ber:>6.3f} | "
              f"{psnr_c:>10.2f} | {status}")

        results.append({
            'qf': qf, 'nc': float(nc), 'ber': float(ber),
            'psnr': float(psnr_c), 'size': float(file_size), 'status': status,
        })
        compressed_images.append(img_compressed.copy())
        extracted_wms.append(wm_extracted.copy())

    return results, compressed_images, extracted_wms


def plot_metrics(results):
    qfs = [r['qf'] for r in results]
    ncs = [r['nc'] for r in results]
    bers = [r['ber'] for r in results]

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Grafik Kinerja Metrik Kuantitatif terhadap Kompresi JPEG',
                 fontsize=14, fontweight='bold')

    ax1.plot(qfs, ncs, marker='o', markersize=8, color='#50c5f1',
             linewidth=2.5, label='NC (Correlation)')
    ax1.axhline(y=NC_THRESHOLD, color='#ff6b6b', linestyle='--',
                linewidth=1.5, label=f'Threshold Valid (NC >= {NC_THRESHOLD})')
    ax1.set_title('Normalized Correlation (NC) vs QF')
    ax1.set_xlabel('Quality Factor (QF)')
    ax1.set_ylabel('Nilai NC')
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_xticks(qfs)
    ax1.invert_xaxis()
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.legend(loc='lower left')

    ax2.plot(qfs, bers, marker='s', markersize=8, color='#5f9f11',
             linewidth=2.5, label='BER (Error Rate)')
    ax2.axhline(y=BER_THRESHOLD, color='#ff6b6b', linestyle='--',
                linewidth=1.5, label=f'Threshold Valid (BER <= {BER_THRESHOLD})')
    ax2.set_title('Bit Error Rate (BER) vs QF')
    ax2.set_xlabel('Quality Factor (QF)')
    ax2.set_ylabel('Nilai BER')
    ax2.set_ylim(-0.05, 0.7)
    ax2.set_xticks(qfs)
    ax2.invert_xaxis()
    ax2.grid(True, linestyle=':', alpha=0.3)
    ax2.legend(loc='upper left')

    fig.tight_layout()
    fig.savefig('reports/grafik_kinerja.png', dpi=200)
    plt.close(fig)
    print("\n[OK] Grafik kinerja disimpan di reports/grafik_kinerja.png")


def plot_visual_analysis(results, compressed_images, extracted_wms):
    plt.style.use('default')
    n = len(results)
    fig, axes = plt.subplots(n, 2, figsize=(10, 3.5 * n))
    fig.suptitle('Analisis Visual Citra Terkompresi & Ekstraksi Watermark',
                 fontsize=14, fontweight='bold', y=0.99)

    for idx, r in enumerate(results):
        img_c = compressed_images[idx]
        wm_bin = extracted_wms[idx]
        status_color = 'green' if r['status'] == 'VALID' else 'red'

        ax_l = axes[idx, 0] if n > 1 else axes[0]
        ax_l.imshow(img_c, cmap='gray')
        ax_l.set_title(f"Foto Terkompresi (QF = {r['qf']})\n"
                       f"Ukuran: {r['size']:.2f} KB | PSNR: {r['psnr']:.2f} dB",
                       fontsize=10)
        ax_l.axis('off')

        ax_r = axes[idx, 1] if n > 1 else axes[1]
        ax_r.imshow(wm_bin, cmap='gray')
        ax_r.set_title(f"Ekstraksi Watermark (QF = {r['qf']})\n"
                       f"NC: {r['nc']:.3f} | BER: {r['ber']:.3f}",
                       fontsize=10)
        ax_r.text(1.05, 0.5, r['status'], transform=ax_r.transAxes,
                  color=status_color, fontweight='bold', fontsize=12,
                  va='center')
        ax_r.axis('off')

    plt.tight_layout()
    fig.savefig('reports/analisis_visual.png', dpi=200)
    plt.close(fig)
    print("[OK] Analisis visual disimpan di reports/analisis_visual.png")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print(f"Cover image  : {img_name}")
    print(f"Watermark    : {wm_name}")

    if not os.path.exists(img_name):
        raise FileNotFoundError(f"File {img_name} tidak ada di folder ini!")
    if not os.path.exists(wm_name):
        raise FileNotFoundError(f"File {wm_name} tidak ada di folder ini!")

    img = cv.imread(img_name, 0)
    if img.shape != (IMG_SIZE, IMG_SIZE):
        print(f"[INFO] Resize {img.shape} -> ({IMG_SIZE}, {IMG_SIZE})")
        img = cv.resize(img, (IMG_SIZE, IMG_SIZE))

    wm = cv.imread(wm_name, 0)
    wm = cv.resize(wm, (W2, W1), interpolation=cv.INTER_NEAREST)
    _, wm = cv.threshold(wm, 127, 255, cv.THRESH_BINARY)
    wm_original = wm.copy()

    print("\n" + "=" * 75)
    print(" EMBEDDING WATERMARK")
    print("=" * 75)
    wmed = watermark_image(img, wm)
    print("Watermarking selesai!")

    print("\n" + "=" * 75)
    print(" EXTRACTING WATERMARK (tanpa kompresi)")
    print("=" * 75)
    wx = extract_watermark(wmed, watermarked_extracted)
    print(f"NC  (no attack): {NCC(wm_original, wx):.4f}")
    print(f"BER (no attack): {BER(wm_original, wx):.4f}")

    results, comp_imgs, ext_wms = evaluate_jpeg_compression(wmed, wm_original)

    plot_metrics(results)
    plot_visual_analysis(results, comp_imgs, ext_wms)

    print("\n" + "=" * 75)
    print(" SELESAI")
    print("=" * 75)
    print("Output:")
    print(f"  - {watermarked_img}        (gambar ber-watermark)")
    print(f"  - {watermarked_extracted}    (watermark hasil ekstraksi)")
    print("  - compressed/                  (gambar tiap QF + watermark ekstraksinya)")
    print("  - reports/grafik_kinerja.png   (NC & BER vs QF)")
    print("  - reports/analisis_visual.png  (analisis visual per QF)")
