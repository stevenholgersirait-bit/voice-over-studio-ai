import os, re, json, uuid, asyncio, shutil, subprocess, tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
AUDIO = DATA / 'audio'
PROJECTS = DATA / 'projects'
AUDIO.mkdir(parents=True, exist_ok=True)
PROJECTS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_MB', '25')) * 1024 * 1024

# Provider abstraction: add Azure/other providers later without changing the UI.
class TTSProvider:
    name = 'base'
    async def synthesize(self, text, voice, rate='+0%', pitch='+0Hz', volume='+0%'):
        raise NotImplementedError

class EdgeTTSProvider(TTSProvider):
    name = 'edge-tts'
    def __init__(self):
        try:
            import edge_tts
            self.edge_tts = edge_tts
        except ImportError:
            self.edge_tts = None

    async def synthesize(self, text, voice, rate='+0%', pitch='+0Hz', volume='+0%'):
        if not self.edge_tts:
            raise RuntimeError('Edge TTS belum terpasang. Jalankan install.bat / pip install -r requirements.txt.')
        out = AUDIO / f'{uuid.uuid4().hex}.mp3'
        communicate = self.edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        await communicate.save(str(out))
        return out

PROVIDER = EdgeTTSProvider()

VOICE_MAP = {
    'id-ID': [
        {'id':'id-ID-ArdiNeural','label':'Male 1 — Ardi','gender':'Male'},
        {'id':'id-ID-GadisNeural','label':'Female 1 — Gadis','gender':'Female'},
    ],
    'en-US': [
    {'id':'en-US-GuyNeural','label':'Male — Guy','gender':'Male'},
    {'id':'en-US-ChristopherNeural','label':'Male Warm — Christopher','gender':'Male'},
    {'id':'en-US-DavisNeural','label':'Male Deep — Davis','gender':'Male'},
    {'id':'en-US-JasonNeural','label':'Male Storytelling — Jason','gender':'Male'},
    {'id':'en-US-TonyNeural','label':'Male Professional — Tony','gender':'Male'},
    {'id':'en-US-SteffanNeural','label':'Male Energetic — Steffan','gender':'Male'},
    {'id':'en-US-JennyNeural','label':'Female — Jenny','gender':'Female'},
    {'id':'en-US-AriaNeural','label':'Female Professional — Aria','gender':'Female'},
    {'id':'en-US-AnaNeural','label':'Female Child — Ana','gender':'Female'},
    {'id':'en-US-SaraNeural','label':'Female Soft — Sara','gender':'Female'},
    ],
    'ja-JP': [
        {'id':'ja-JP-KeitaNeural','label':'Male 1 — Keita','gender':'Male'},
        {'id':'ja-JP-NanamiNeural','label':'Female 1 — Nanami','gender':'Female'},
    ],
    'zh-CN': [
        {'id':'zh-CN-YunxiNeural','label':'Male 1 — Yunxi','gender':'Male'},
        {'id':'zh-CN-XiaoxiaoNeural','label':'Female 1 — Xiaoxiao','gender':'Female'},
    ],
    'ko-KR': [
        {'id':'ko-KR-InJoonNeural','label':'Male 1 — InJoon','gender':'Male'},
        {'id':'ko-KR-SunHiNeural','label':'Female 1 — SunHi','gender':'Female'},
    ],
    'fr-FR': [
        {'id':'fr-FR-HenriNeural','label':'Male 1 — Henri','gender':'Male'},
        {'id':'fr-FR-DeniseNeural','label':'Female 1 — Denise','gender':'Female'},
    ],
    'es-ES': [
        {'id':'es-ES-AlvaroNeural','label':'Male 1 — Alvaro','gender':'Male'},
        {'id':'es-ES-ElviraNeural','label':'Female 1 — Elvira','gender':'Female'},
    ],
    'jv-ID': [
        {'id':'jv-ID-DimasNeural','label':'Male — Dimas','gender':'Male'},
        {'id':'jv-ID-SitiNeural','label':'Female — Siti','gender':'Female'},
    ],
    'su-ID': [
        {'id':'su-ID-JajangNeural','label':'Male — Jajang','gender':'Male'},
        {'id':'su-ID-TutiNeural','label':'Female — Tuti','gender':'Female'},
    ],
}

LANGUAGES = [
    {'id':'id-ID','label':'🇮🇩 Bahasa Indonesia'}, {'id':'en-US','label':'🇬🇧 English'},
    {'id':'ja-JP','label':'🇯🇵 Japanese'}, {'id':'zh-CN','label':'🇨🇳 Chinese'},
    {'id':'ko-KR','label':'🇰🇷 Korean'}, {'id':'fr-FR','label':'🇫🇷 French'},
    {'id':'es-ES','label':'🇪🇸 Spanish'}, {'id':'jv-ID','label':'🟤 Jawa'}, {'id':'su-ID','label':'🟢 Sunda'}
]

EMOTIONS = {
    'Natural': {'rate':0,'pitch':0,'direction':'natural, conversational, clear'},
    'Happy': {'rate':8,'pitch':2,'direction':'bright, cheerful, smiling energy'},
    'Sad': {'rate':-8,'pitch':-2,'direction':'soft, restrained, emotionally heavy'},
    'Angry': {'rate':10,'pitch':3,'direction':'firm, intense, controlled anger'},
    'Dramatic': {'rate':-7,'pitch':-2,'direction':'controlled dramatic intensity with deliberate pauses'},
    'Tense': {'rate':4,'pitch':1,'direction':'tense, alert, slightly urgent'},
    'Warm': {'rate':-2,'pitch':1,'direction':'warm, intimate and reassuring'},
    'Funny': {'rate':9,'pitch':3,'direction':'playful, lively, lightly exaggerated'},
    'Calm': {'rate':-10,'pitch':-1,'direction':'calm, relaxed and spacious'},
    'Energetic': {'rate':15,'pitch':3,'direction':'high energy, crisp and engaging'},
    'Cinematic': {'rate':-8,'pitch':-2,'direction':'cinematic, spacious, powerful reveals'},
    'Storytelling': {'rate':-6,'pitch':0,'direction':'natural storyteller with scene-aware pacing'},
    'Professional': {'rate':0,'pitch':0,'direction':'polished, confident, articulate'},
    'News': {'rate':2,'pitch':0,'direction':'clear, authoritative broadcast delivery'},
    'Advertisement': {'rate':8,'pitch':2,'direction':'persuasive, energetic commercial delivery'},
}

VOICE_CHARACTERS = {
    'Natural': {'rate': 0, 'pitch': 0},
    'Deep': {'rate': -8, 'pitch': -4},
    'Cinematic': {'rate': -10, 'pitch': -3},
    'Storyteller': {'rate': -6, 'pitch': -1},
    'News': {'rate': 2, 'pitch': 0},
    'Energetic': {'rate': 12, 'pitch': 2},
    'Calm': {'rate': -10, 'pitch': -2},
    'Dramatic': {'rate': -5, 'pitch': -3},
    'Young': {'rate': 8, 'pitch': 4},
    'Older': {'rate': -12, 'pitch': -5},
}

STYLES = ['Natural','Storytelling','Cinematic','YouTube','TikTok','Advertisement']
FILM_STYLES = ['Slow Storytelling','Normal Storytelling','Fast Storytelling','Cinematic Storytelling']


def clamp(n, lo, hi): return max(lo, min(hi, n))

def chunks(text, max_chars=2800):
    text = re.sub(r'\r\n?', '\n', text).strip()
    if not text: return []
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    out=[]; current=''
    def flush():
        nonlocal current
        if current.strip(): out.append(current.strip())
        current=''
    for p in paras:
        if len(p) <= max_chars and len(current)+len(p)+2 <= max_chars:
            current = (current+'\n\n'+p).strip(); continue
        if current: flush()
        if len(p) <= max_chars: current=p; continue
        sentences = re.split(r'(?<=[.!?…])\s+', p)
        for s in sentences:
            if len(s) <= max_chars and len(current)+len(s)+1 <= max_chars:
                current=(current+' '+s).strip()
            else:
                if current: flush()
                # fallback word-safe packing
                words=s.split()
                buf=''
                for w in words:
                    if len(buf)+len(w)+1 <= max_chars: buf=(buf+' '+w).strip()
                    else:
                        if buf: out.append(buf)
                        buf=w
                current=buf
    if current: flush()
    return out


def smart_text(text, pause='Short', film_mode=False):
    # Keep words intact; use punctuation that Edge TTS naturally interprets.
    text = re.sub(r'\s+', ' ', text.strip())
    if pause == 'Medium': text = re.sub(r'\.\s+', '. … ', text)
    elif pause == 'Long': text = re.sub(r'\.\s+', '. … … ', text)
    if film_mode:
        text = re.sub(r'\n+', '. … ', text)
    return text


def voice_params(voice_id, emotion, speed, pitch, volume, emotion_intensity=70, character='Natural'):
    e = EMOTIONS.get(emotion, EMOTIONS['Natural'])
    c = VOICE_CHARACTERS.get(character, VOICE_CHARACTERS['Natural'])

    intensity = clamp(float(emotion_intensity), 0, 100) / 100.0
    rate = clamp(float(speed), 0.5, 2.0)

    # Base speed + character + emotion
    rate_pct = clamp(
        (rate - 1) * 100 +
        c['rate'] +
        e['rate'] * intensity,
        -50,
        100
    )

    # Base pitch + character + emotion
    pitch_val = clamp(
        float(pitch) +
        c['pitch'] +
        e['pitch'] * intensity,
        -20,
        20
    )

    vol_pct = clamp(float(volume), 0, 100)

    # Edge TTS uses volume as percentage offset
    vol_offset = vol_pct - 100

    return (
        f'{rate_pct:+.0f}%',
        f'{pitch_val:+.0f}Hz',
        f'{vol_offset:+.0f}%'
    )

def ffmpeg_concat(files, out_file):
    list_file = Path(tempfile.mkstemp(suffix='.txt')[1])
    try:
        with open(list_file,'w',encoding='utf-8') as f:
            for p in files: f.write("file '%s'\n" % str(Path(p).resolve()).replace("'", "'\\''"))
        cmd=['ffmpeg','-y','-f','concat','-safe','0','-i',str(list_file),'-c','copy',str(out_file)]
        r=subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode!=0:
            raise RuntimeError('Audio merge failed')
    finally:
        list_file.unlink(missing_ok=True)


def simple_enhance(text, mode):
    # Offline fallback. If OPENAI_API_KEY exists, /api/ai-enhance uses the model instead.
    t=re.sub(r'[ \t]+',' ',text.strip())
    t=re.sub(r'([.!?])([A-Za-zÀ-ÿ])', r'\1 \2', t)
    if mode in ('Storytelling','Cinematic','YouTube'):
        t=re.sub(r'\n{2,}', '\n\n', t)
    return t

def simple_director(text):
    sentences=re.split(r'(?<=[.!?…])\s+', text.strip())
    lines=[]
    for i,s in enumerate(sentences):
        if not s: continue
        low=s.lower()
        tag='CALM'
        if any(x in low for x in ['namun','tetapi','tiba-tiba','ternyata','kebenaran','rahasia','akhirnya','sayangnya']): tag='DRAMATIC'
        if '?' in s: tag='INTENSE'
        lines.append(f'[{tag}] {s}')
        if i < len(sentences)-1: lines.append('[PAUSE]')
    return '\n'.join(lines)

async def synthesize_job(text, voice, emotion, speed, pitch, volume, emotion_intensity, pause, film_mode, film_style, character='Natural'):
    processed=smart_text(text,pause,film_mode)
    parts=chunks(processed)
    if not parts: raise ValueError('Script kosong')
    film_speed={'Slow Storytelling':0.82,'Normal Storytelling':1.0,'Fast Storytelling':1.18,'Cinematic Storytelling':0.9}.get(film_style,1.0) if film_mode else 1.0
    rate, p, vol = voice_params(
    voice,
    emotion,
    speed * film_speed,
    pitch,
    volume,
    emotion_intensity,
    character
)
    files=[]
    try:
        for part in parts:
            files.append(await PROVIDER.synthesize(part, voice, rate, p, vol))
        final=AUDIO / f'{uuid.uuid4().hex}.mp3'
        if len(files)==1: shutil.copy2(files[0],final)
        else: ffmpeg_concat(files,final)
        return final, len(parts)
    finally:
        for f in files:
            Path(f).unlink(missing_ok=True)

@app.get('/')
def index(): return render_template('index.html')

@app.get('/api/config')
def config():
    return jsonify({
    'languages': LANGUAGES,
    'voices': VOICE_MAP,
    'emotions': list(EMOTIONS.keys()),
    'characters': list(VOICE_CHARACTERS.keys()),
    'styles': STYLES,
    'filmStyles': FILM_STYLES,
    'provider': PROVIDER.name,
    'aiConfigured': bool(os.getenv('OPENAI_API_KEY'))
})

@app.post('/api/generate')
def generate():
    data=request.get_json(force=True)
    text=data.get('text','').strip()
    if not text: return jsonify({'error':'Naskah masih kosong.'}),400
    voice=data.get('voice','id-ID-ArdiNeural')
    emotion=data.get('emotion','Natural')
    character=data.get('character','Natural')
    try:
        speed=float(data.get('speed',1)); pitch=float(data.get('pitch',0)); volume=float(data.get('volume',100))
    except: return jsonify({'error':'Pengaturan suara tidak valid.'}),400
    pause=data.get('pause','Short'); film=bool(data.get('filmMode')); emotion_intensity=float(data.get('emotionIntensity',70)); film_style=data.get('filmStyle','Normal Storytelling')
    try:
        final,count=asyncio.run(
    synthesize_job(
        text,
        voice,
        emotion,
        speed,
        pitch,
        volume,
        emotion_intensity,
        pause,
        film,
        film_style,
        character
    )
)
        rid=final.stem
        wav=AUDIO / f'{rid}.wav'
        try:
            subprocess.run(['ffmpeg','-y','-i',str(final),'-ar','44100','-ac','2',str(wav)],capture_output=True,check=True)
        except Exception:
            wav=None
        title=data.get('title') or text[:48].replace('\n',' ')
        item={'id':rid,'title':title,'createdAt':datetime.now().isoformat(timespec='seconds'),'voice':voice,'language':data.get('language','id-ID'),'emotion':emotion,'duration':'—','url':f'/audio/{final.name}','wavUrl':f'/audio/{wav.name}' if wav else None,'chunks':count}
        (PROJECTS / f'{rid}.json').write_text(json.dumps({'history':item,'script':text,'settings':data},ensure_ascii=False,indent=2),encoding='utf-8')
        return jsonify(item)
    except Exception:
        return jsonify({'error':'Voice over belum berhasil dibuat. Silakan coba lagi.'}),500

@app.get('/api/history')
def history():
    items=[]
    for p in sorted(PROJECTS.glob('*.json'), key=lambda x:x.stat().st_mtime, reverse=True):
        try:
            d=json.loads(p.read_text(encoding='utf-8')); h=d.get('history');
            if h: items.append(h)
        except: pass
    return jsonify(items[:100])

@app.delete('/api/history/<rid>')
def delete_history(rid):
    p=PROJECTS/f'{rid}.json'
    if p.exists():
        try:
            d=json.loads(p.read_text(encoding='utf-8')); url=d.get('history',{}).get('url',''); Path(BASE / url.lstrip('/')).unlink(missing_ok=True)
        except: pass
        p.unlink(missing_ok=True)
    return jsonify({'ok':True})

@app.get('/api/project/<rid>')
def get_project(rid):
    p=PROJECTS/f'{rid}.json'
    if not p.exists(): return jsonify({'error':'Project tidak ditemukan.'}),404
    return jsonify(json.loads(p.read_text(encoding='utf-8')))

@app.post('/api/project')
def save_project():
    data=request.get_json(force=True); pid=data.get('id') or uuid.uuid4().hex
    data['id']=pid; data['updatedAt']=datetime.now().isoformat(timespec='seconds')
    (PROJECTS/f'project-{pid}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return jsonify({'ok':True,'id':pid})

@app.get('/api/projects')
def projects():
    out=[]
    for p in sorted(PROJECTS.glob('project-*.json'), key=lambda x:x.stat().st_mtime, reverse=True):
        try: out.append(json.loads(p.read_text(encoding='utf-8')))
        except: pass
    return jsonify(out[:100])

@app.delete('/api/project/<pid>')
def delete_project(pid):
    (PROJECTS/f'project-{pid}.json').unlink(missing_ok=True)
    return jsonify({'ok':True})

@app.post('/api/ai-enhance')
def ai_enhance():
    data=request.get_json(force=True); text=data.get('text','').strip(); mode=data.get('mode','Natural')
    if not text: return jsonify({'error':'Naskah masih kosong.'}),400
    key=os.getenv('OPENAI_API_KEY')
    if not key: return jsonify({'text':simple_enhance(text,mode),'fallback':True,'message':'AI provider belum dikonfigurasi; digunakan Smart Script fallback.'})
    try:
        import requests
        model=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
        prompt=f'''Improve this voice-over script in {mode} mode. Preserve the original meaning, facts, names and sequence. Only improve punctuation, sentence flow, pauses, transitions, and spoken naturalness. Return only the revised script in the same language as the input. Do not add commentary.\n\nSCRIPT:\n{text}'''
        r=requests.post('https://api.openai.com/v1/responses',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'input':prompt},timeout=120)
        r.raise_for_status(); obj=r.json(); out=obj.get('output_text','').strip()
        return jsonify({'text':out or text,'fallback':False})
    except Exception:
        return jsonify({'text':simple_enhance(text,mode),'fallback':True,'message':'Voice over AI belum berhasil dipanggil; digunakan Smart Script fallback.'})

@app.post('/api/voice-director')
def voice_director():
    data=request.get_json(force=True); text=data.get('text','').strip()
    if not text: return jsonify({'error':'Naskah masih kosong.'}),400
    key=os.getenv('OPENAI_API_KEY')
    if not key: return jsonify({'direction':simple_director(text),'fallback':True})
    try:
        import requests
        model=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
        prompt='''Analyze this voice-over script and annotate it for a TTS engine. Preserve every word exactly; only add line-level direction tags like [CALM], [DRAMATIC], [INTENSE], [PAUSE], [PAUSE LONG], [FAST], [SLOW], [EMPHASIS]. Do not rewrite or remove words. Return only annotated script.\n\n'''+text
        r=requests.post('https://api.openai.com/v1/responses',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'input':prompt},timeout=120)
        r.raise_for_status(); out=r.json().get('output_text','').strip()
        return jsonify({'direction':out or simple_director(text),'fallback':False})
    except Exception:
        return jsonify({'direction':simple_director(text),'fallback':True})

@app.get('/audio/<path:filename>')
def audio(filename): return send_from_directory(AUDIO, filename, as_attachment=False)

if __name__=='__main__':
    host=os.getenv('HOST','0.0.0.0'); port=int(os.getenv('PORT','5000'))
    app.run(host=host,port=port,debug=False)
