# Cara paling mudah membuat VOICE OVER STUDIO AI menjadi website online

## Pilihan yang direkomendasikan: Render

Render mendukung aplikasi Flask/Python dan menyediakan Web Service gratis untuk prototipe. Paket ini sudah dilengkapi Dockerfile sehingga FFmpeg dan Edge TTS dipasang otomatis.

### Yang perlu dilakukan

1. Buat akun GitHub di https://github.com/ jika belum punya.
2. Buat repository baru bernama `voice-over-studio-ai`.
3. Pilih **Add file → Upload files**.
4. Upload SEMUA isi folder aplikasi ini (bukan file ZIP-nya).
5. Klik **Commit changes**.
6. Buka https://dashboard.render.com/ lalu login dengan GitHub.
7. Pilih **New → Web Service**.
8. Pilih repository `voice-over-studio-ai`.
9. Render akan membaca `Dockerfile`.
10. Pilih paket **Free** untuk uji coba.
11. Klik **Create Web Service**.
12. Tunggu deployment selesai.
13. Render akan memberikan alamat seperti `https://voice-over-studio-ai.onrender.com`.

### OpenAI API (opsional)

Aplikasi tetap dapat membuat voice over tanpa OpenAI API key karena TTS memakai Edge TTS.

Jika ingin mengaktifkan **Improve Script** dan **AI Voice Director** dengan OpenAI:

- Render → service → Environment
- Tambahkan:
  - `OPENAI_API_KEY` = API key Anda
  - `OPENAI_MODEL` = `gpt-5.6-luna`
- Save changes → redeploy

Jangan pernah memasukkan API key ke `static/app.js` atau HTML.

## Catatan penting

Render Free cocok untuk testing/hobby. Service dapat tidur setelah tidak ada trafik dan filesystem lokal tidak permanen. Karena itu, untuk penggunaan serius kita sebaiknya V2 memakai database dan object storage.
