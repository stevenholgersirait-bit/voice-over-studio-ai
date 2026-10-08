# VOICE OVER STUDIO AI — MVP

Aplikasi web TTS studio untuk YouTube, TikTok, Shorts, storytelling, narasi film, iklan, dan konten media sosial.

## Yang sudah berfungsi
- UI dark premium responsive desktop/HP
- Text editor panjang + character/word counter
- Paste / Clear
- Auto-chunking: paragraf → kalimat → kata, tanpa memotong kata
- TTS MP3 melalui Edge TTS
- Bahasa Indonesia, English, Japanese, Chinese, Korean, French, Spanish, Jawa, Sunda
- Voice list hanya berisi voice yang didefinisikan sebagai tersedia untuk provider MVP
- Emotion/vibe → rate/pitch/volume mapping
- Film Story Mode + storytelling speed presets (UI)
- Speed, pitch, volume, emotion intensity controls
- Smart punctuation / pause handling
- Preview, play/pause/stop, progress, download MP3
- Voice History + delete
- Projects: save/open/delete script + settings
- Improve Script: fallback offline; bisa memakai OpenAI Responses API bila OPENAI_API_KEY dipasang
- AI Voice Director: fallback offline; bisa memakai OpenAI Responses API bila OPENAI_API_KEY dipasang
- API key hanya dibaca server-side dari .env
- Provider abstraction di backend agar TTS bisa diganti

## Kenapa Edge TTS?
MVP ini sengaja tidak membutuhkan API key untuk TTS. Paket `edge-tts` menyediakan akses Python ke layanan online text-to-speech Microsoft Edge. Untuk bahasa lokal, provider yang mendasarinya menyediakan suara Javanese dan Sundanese; daftar suara dapat berubah sehingga jangan menganggap semua nama voice UI sebagai permanen.

> Penting: “gratis” di sini berarti MVP tidak meminta API key berbayar. Layanan online tetap memiliki ketentuan penggunaan dan ketersediaan yang dapat berubah. Jangan mengklaim unlimited commercial usage tanpa memeriksa terms provider.

## Cara paling mudah di Windows
1. Pastikan Python 3.11+ terpasang.
2. Extract folder ini.
3. Klik dua kali `start_windows.bat`.
4. Tunggu instalasi selesai.
5. Browser buka `http://127.0.0.1:5000`.

Script akan otomatis membuat virtual environment dan memasang dependency.

## macOS / Linux
Buka Terminal pada folder aplikasi, lalu jalankan:

```bash
./start_mac_linux.sh
```

Buka `http://127.0.0.1:5000`.

## AI Script Enhancer + AI Voice Director
Kedua fitur dapat berjalan dalam mode fallback tanpa API key. Jika ingin AI model sungguhan:

1. Buka file `.env` (dibuat otomatis dari `.env.example`).
2. Isi `OPENAI_API_KEY=...` dengan API key milik Anda.
3. Opsional ubah `OPENAI_MODEL` ke model yang tersedia di akun Anda.
4. Restart aplikasi.

API key tidak dikirim ke browser dan tidak ditampilkan di UI.

## Catatan WAV
MVP ini menghasilkan MP3 agar instalasi sederhana. Tombol WAV diberi pesan bahwa provider MVP belum melakukan export WAV. Untuk versi berikutnya dapat ditambahkan pipeline FFmpeg/PCM atau provider cloud yang mengembalikan WAV langsung.

## Arsitektur
```text
Browser UI
   ↓
Flask API
   ├── TTSProvider
   │    └── EdgeTTSProvider (MVP)
   ├── optional OpenAI Responses API
   ├── Chunker
   ├── Audio merger (FFmpeg)
   └── Local JSON project/history storage
```

## Deployment
Untuk pemakaian pribadi, jalankan di komputer sendiri. Untuk deployment publik, gunakan VPS/Render/Railway/Fly.io atau platform Python lain, pasang FFmpeg, simpan `.env` sebagai secret, dan pindahkan storage project/audio ke object storage/database.

Jangan menjalankan development server Flask sebagai server produksi internet-facing.
