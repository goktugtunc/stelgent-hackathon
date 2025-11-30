import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Code2, Sparkles, FolderOpen, Loader2 } from 'lucide-react';

export default function HomeView({ isConnectingWallet, onConnectWallet }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center gap-2">
          <Code2 className="h-8 w-8 text-purple-400" />
          <h1 className="text-2xl font-bold text-white">Stelgent</h1>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => {
              console.log('Header buton tıklandı');
              onConnectWallet();
            }}
            disabled={isConnectingWallet}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {isConnectingWallet ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Bağlanıyor...
              </>
            ) : (
              <>🌟 Connect with Freighter</>
            )}
          </Button>
        </div>
      </header>

      {/* Hero */}
      <div className="container mx-auto px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold text-white mb-6 leading-tight">
            AI ile <span className="text-purple-400">Website</span> Oluştur
            <br />
            <span className="text-blue-400">Stellar</span> ile Bağlan
          </h1>
          <p className="text-xl text-gray-300 mb-12 leading-relaxed">
            Yapay zeka destekli kod üretimi ile saniyeler içinde profesyonel websiteleri
            oluşturun. Freighter wallet ile güvenli şekilde bağlanın, projelerinizi Docker
            container&apos;larında çalıştırın.
          </p>

          <div className="flex justify-center gap-4 mb-16">
            <Button
              onClick={() => {
                console.log('Hero buton tıklandı');
                onConnectWallet();
              }}
              disabled={isConnectingWallet}
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-4 text-lg"
            >
              {isConnectingWallet ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Bağlanıyor...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Freighter ile Başla
                </>
              )}
            </Button>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 text-left">
            <Card className="bg-gray-800 border-gray-700 p-6">
              <CardHeader className="pb-3">
                <Code2 className="h-8 w-8 text-purple-400 mb-2" />
                <CardTitle className="text-white">AI Kod Üretimi</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  GPT-4o ile güçlü AI teknolojisi kullanarak istediğiniz websiteyi dakikalar
                  içinde oluşturun.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-800 border-gray-700 p-6">
              <CardHeader className="pb-3">
                <Sparkles className="h-8 w-8 text-blue-400 mb-2" />
                <CardTitle className="text-white">Stellar Entegrasyonu</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Freighter wallet ile güvenli giriş yapın, projelerinizi blockchain
                  teknolojisi ile koruyun.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-800 border-gray-700 p-6">
              <CardHeader className="pb-3">
                <FolderOpen className="h-8 w-8 text-green-400 mb-2" />
                <CardTitle className="text-white">Docker Deploy</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Projelerinizi otomatik olarak Docker container&apos;larında deploy edin ve
                  gerçek zamanlı test edin.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
