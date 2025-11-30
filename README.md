
# Stelgent Monorepo – AI-Powered Code Generation & NFT Marketplace

Stelgent, geliştiricilerin ve ekiplerin tam yığın uygulamaları **yapay zeka destekli** olarak tasarlayıp inşa edebildiği, VSCode benzeri bir web IDE’sidir.  
Bu monorepo aynı zamanda Stelgent projelerini **NFT olarak mint etmeye ve listelemeye** yarayan NFT Marketi de içerir.

Bu belge; projenin ne olduğunu, hangi alt bileşenlerden oluştuğunu ve temel çalışma mantığını özetler. Kurulum adımları, geliştirme ortamını hızlıca ayağa kaldırmanıza yardımcı olacak şekilde tasarlanmıştır.

---

## İçindekiler

- [Mimari Genel Bakış](#mimari-genel-bakış)
- [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
- [Dizin Yapısı](#dizin-yapısı)
- [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
  - [Ortak Gereksinimler](#ortak-gereksinimler)
  - [Backend (FastAPI)](#backend-fastapi)
  - [Stelgent Frontend](#stelgent-frontend)
  - [NFT Market Frontend](#nft-market-frontend)
- [Çalışma Akışları](#çalışma-akışları)
  - [1. Stelgent ile Proje Oluşturma](#1-stelgent-ile-proje-oluşturma)
  - [2. Projeyi NFT Olarak Mint Etme](#2-projeyi-nft-olarak-mint-etme)
  - [3. NFT Market Üzerinden Proje Satın Alma](#3-nft-market-üzerinden-proje-satın-alma)
- [Konfigürasyon Değişkenleri](#konfigürasyon-değişkenleri)
- [Geliştirme Akışı](#geliştirme-akışı)
- [Lisans](#lisans)

---

## Mimari Genel Bakış

Monorepo kabaca üç ana parçadan oluşur:

1. **Backend (FastAPI + MongoDB)**  
   - Kullanıcılar, projeler, AI oturumları ve NFT metadata’larını yönetir.  
   - Yapay zeka entegrasyonu, proje dosyalarının saklanması ve iş mantığı bu katmandadır.

2. **Stelgent Frontend (Next.js)**  
   - VSCode benzeri web IDE’yi, proje yöneticisini ve AI sohbet arayüzünü sunar.  
   - Kullanıcıların projelerini yönetmesine, AI ile konuşmasına ve proje çıktısını görmesine olanak tanır.  
   - “Mint as NFT” gibi aksiyonları backend API’si üzerinden tetikler.

3. **NFT Market Frontend (Next.js)**  
   - Soroban tabanlı akıllı sözleşme ile mint edilmiş NFT’leri listeler.  
   - Her NFT, bir Stelgent projesini ve onun metadata’sını temsil eder.  
   - Kullanıcılar bu arayüz üzerinden projeleri görüntüleyebilir, detay sayfasına gidebilir ve satın alma akışını başlatabilir.

İsteğe bağlı olarak ayrıca:

4. **Akıllı Sözleşmeler (Soroban / Stellar)**  
   - NFT mint etme, sahiplik ve transfer mantığı bu katmandadır.  
   - Backend ve NFT Market, bu sözleşme ile RPC üzerinden konuşur.

---

## Öne Çıkan Özellikler

- **Yapay Zeka Destekli Kod Üretimi**
  - Çok turlu sohbet ile backend, frontend veya tam yığın projeler oluşturma.
  - Proje yapısını koruyan, dosya bazlı kod güncellemeleri.

- **Web IDE Deneyimi**
  - VSCode benzeri düzen: dosya ağacı, editör sekmeleri, terminal benzeri çıktı alanı.
  - Projeyi hızlıca gözden geçirmek için kod önizlemeleri.

- **Projeden NFT’ye Doğru Akış**
  - Kullanıcı Stelgent’te bir proje oluşturur.
  - “Mint” aksiyonu ile proje metadata’sı IPFS benzeri bir depoya yüklenir.
  - Soroban akıllı sözleşmesi üzerinden NFT basılır (mint).
  - NFT Market, bu NFT’yi otomatik olarak listeler.

- **NFT Market Entegrasyonu**
  - Proje NFT’leri; fiyat, açıklama ve teknik stack bilgisi ile birlikte gösterilir.
  - Koleksiyon mantığı ile projeleri vitrin görünümünde sunar.

---

## Dizin Yapısı

Örnek bir dizin yapısı aşağıdaki gibidir (gerçek repo yapınız değişiklik gösterebilir):

```bash
.
├── backend/                 # FastAPI backend uygulaması
│   ├── app/
│   ├── requirements.txt
│   └── main.py
├── frontend/                # Stelgent ana frontend (Next.js)
│   ├── src/
│   ├── package.json
│   └── next.config.mjs
├── nft-market-frontend/     # NFT Market arayüzü (Next.js)
│   ├── src/
│   ├── package.json
│   └── next.config.mjs
└── contracts/               # Soroban akıllı sözleşme kaynakları (opsiyonel)
    └── ...
```

---

## Kurulum ve Çalıştırma

### Ortak Gereksinimler

- **Node.js**: v18+ veya v20+ (Next.js 16 için önerilen sürümler)
- **Python**: 3.11+
- **MongoDB**: 7.x veya uyumlu bir sürüm
- `npm` veya `pnpm` (frontend projeleri için)
- Geliştirme ortamında `.env` dosyalarının tanımlanmış olması

> Not: Aşağıdaki komutlar örnektir; kendi dizin yapınıza göre klasör isimleri değişebilir.

---

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Gerekli ortam değişkenlerini `.env` dosyanıza ekleyin (aşağıdaki [Konfigürasyon Değişkenleri](#konfigürasyon-değişkenleri) bölümüne bakın).

Backend’i başlatmak için:

```bash
uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

API varsayılan olarak `http://localhost:8005` üzerinde çalışacaktır.

---

### Stelgent Frontend

```bash
cd frontend
npm install        # veya pnpm install
npm run dev
```

Geliştirme modunda varsayılan port genellikle `3000` veya bir sonraki uygun porttur.  
`.env.local` dosyasında backend adresini aşağıdaki gibi tanımladığınızdan emin olun:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8005
```

---

### NFT Market Frontend

```bash
cd nft-market-frontend
npm install        # veya pnpm install
npm run dev
```

Varsayılan olarak `3001` veya `3002` gibi başka bir portta çalışabilir.  
`.env.local` içerisine, Soroban RPC adresi ve kontrat kimliğini ekleyin:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8005
NEXT_PUBLIC_RPC_URL=https://soroban-testnet.stellar.org
NEXT_PUBLIC_NETWORK_PASSPHRASE=Test SDF Network ; September 2015
NEXT_PUBLIC_NFT_CONTRACT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_IPFS_GATEWAY=https://ipfs.io/ipfs
```

---

## Çalışma Akışları

### 1. Stelgent ile Proje Oluşturma

1. Kullanıcı Stelgent frontend üzerinden giriş yapar veya kayıt olur.
2. Yeni bir proje oluşturur (örneğin “NFT Marketplace API”).
3. “AI Chat” alanında, oluşturmak istediği servis veya uygulamayı tarif eder.
4. Backend, OpenAI entegrasyonu üzerinden kod önerilerini üretir.
5. Üretilen kod:
   - Proje dosya ağacına kaydedilir.
   - İstenirse kullanıcı tarafından düzenlenebilir.
6. Kullanıcı proje tamamlandığında, “Mint as NFT” benzeri bir buton üzerinden NFT sürecini başlatabilir.

### 2. Projeyi NFT Olarak Mint Etme

1. Kullanıcı mint ekranında:
   - **Fiyat** (örneğin STLGENT veya benzeri token cinsinden),
   - **Açıklama** (projenin ne sunduğu),
   - Gerekirse ek metadata alanlarını doldurur.
2. Frontend bu verileri backend’e gönderir.
3. Backend tarafında:
   - Projenin ilgili metadata’sı hazırlanır (isim, açıklama, IPFS hash, repo bilgisi vb.).
   - Dosyalar veya özet veriler IPFS benzeri bir depoya yüklenir.
   - Soroban RPC üzerinden ilgili NFT akıllı sözleşmesine **mint** çağrısı yapılır.
4. Akıllı sözleşme:
   - Yeni bir token ID üretir.
   - Sahipliği mint eden kullanıcıya atar.
   - Metadata referansını saklar.
5. Başarılı mint işleminden sonra:
   - Backend, proje ile NFT arasındaki ilişkiyi veritabanına kaydeder.
   - NFT Market, bu yeni NFT’yi listeleyebilir hale gelir.

### 3. NFT Market Üzerinden Proje Satın Alma

1. Ziyaretçi veya kullanıcı, NFT Market arayüzüne girer.
2. Liste sayfasında tüm aktif proje NFT’lerini görür:
   - Proje adı
   - Fiyat
   - Kısa açıklama
   - Gerekirse teknoloji etiketleri (React, FastAPI, Web3 vb.)
3. Detay sayfasına geçtiğinde:
   - Projenin daha geniş açıklamasını,
   - Mint bilgilerini,
   - Satın alma butonunu görür.
4. Satın alma süreci:
   - Kullanıcı cüzdanı (ör. Freighter) ile bağlantı kurar.
   - Akıllı sözleşmeye gerekli fon transferi yapılır.
   - Sözleşme, NFT sahipliğini yeni alıcıya devreder.
5. İşlem tamamlandıktan sonra:
   - Market arayüzü yeni sahibi yansıtacak şekilde güncellenir.
   - İsteğe bağlı olarak backend’de raporlama ve loglama yapılır.

---

## Konfigürasyon Değişkenleri

Aşağıdaki değişken isimleri örnek amaçlıdır; kendi proje ayarlarınızla eşleştirerek kullanabilirsiniz.

### Backend `.env` Örneği

```env
# Uygulama
APP_ENV=development
APP_PORT=8005

# MongoDB
MONGODB_URI=mongodb://localhost:27017/stelgent

# JWT / Kimlik Doğrulama
JWT_SECRET=super-secret-key
JWT_EXPIRES_IN=3600

# OpenAI / AI Entegrasyonu
OPENAI_API_KEY=sk-...

# Stellar / Soroban
STELLAR_NETWORK=testnet
SOROBAN_RPC_URL=https://soroban-testnet.stellar.org
NFT_CONTRACT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# IPFS / Depolama
IPFS_API_URL=http://localhost:5001/api/v0
IPFS_GATEWAY_URL=https://ipfs.io/ipfs
```

### Frontend `.env.local` Örneği (Stelgent)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8005
NEXT_PUBLIC_STELLAR_NETWORK=testnet
NEXT_PUBLIC_SOROBAN_RPC_URL=https://soroban-testnet.stellar.org
```

### NFT Market `.env.local` Örneği

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8005
NEXT_PUBLIC_RPC_URL=https://soroban-testnet.stellar.org
NEXT_PUBLIC_NETWORK_PASSPHRASE=Test SDF Network ; September 2015
NEXT_PUBLIC_NFT_CONTRACT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_IPFS_GATEWAY=https://ipfs.io/ipfs
```

---

## Geliştirme Akışı

1. **Backend’i başlatın**  
   - `uvicorn main:app --reload --port 8005`

2. **Stelgent Frontend’i başlatın**  
   - `cd frontend && npm run dev`

3. **NFT Market Frontend’i başlatın**  
   - `cd nft-market-frontend && npm run dev`

4. Geliştirme sürecinde:
   - API ve frontend loglarını takip edin.
   - Kontrat adresi veya ağ ayarlarını değiştirdiğinizde ilgili `.env` dosyalarını güncelleyin.
   - Yeni özellikler eklerken hem Stelgent arayüzünü, hem de NFT Market akışlarını göz önünde bulundurun.

---

## Lisans

Bu proje MIT lisansı altında dağıtılmaktadır. Ayrıntılar için `LICENSE` dosyasına bakabilirsiniz.
