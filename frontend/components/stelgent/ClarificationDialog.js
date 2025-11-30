import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';

export default function ClarificationDialog({
  open,
  onOpenChange,
  question,
  field,
  answer,
  setAnswer,
  isLoading,
  onSubmit,
}) {
  const toggleMultiOption = (option) => {
    const current = answer.split(', ').filter(Boolean);
    if (current.includes(option)) {
      setAnswer(current.filter((o) => o !== option).join(', '));
    } else {
      setAnswer([...current, option].join(', '));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gray-800 border-gray-700 text-white">
        <DialogHeader>
          <DialogTitle className="text-purple-400">Bilgi Gerekli</DialogTitle>
          <DialogDescription className="text-gray-300">
            Projeyi doğru şekilde oluşturmak için birkaç bilgiye ihtiyaç var.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-600">
            <p className="text-sm text-gray-300 mb-4">{question}</p>

            {field === 'pages' && (
              <div className="grid grid-cols-2 gap-2">
                {[
                  'Ana sayfa',
                  'Oyun listesi',
                  'Profil sayfası',
                  'Puan tablosu',
                  'Giriş/Kayıt',
                  'Mağaza',
                  'Hakkında',
                  'İletişim',
                ].map((option) => (
                  <Button
                    key={option}
                    variant={answer.includes(option) ? 'default' : 'outline'}
                    onClick={() => toggleMultiOption(option)}
                    className={`text-sm ${
                      answer.includes(option)
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}

            {field === 'theme' && (
              <div className="grid grid-cols-3 gap-2">
                {[
                  'Modern',
                  'Neon/Cyberpunk',
                  'Retro/Vintage',
                  'Minimal',
                  'Dark',
                  'Colorful',
                ].map((option) => (
                  <Button
                    key={option}
                    variant={answer === option ? 'default' : 'outline'}
                    onClick={() => setAnswer(option)}
                    className={`text-sm ${
                      answer === option
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}

            {field === 'platform' && (
              <div className="grid grid-cols-2 gap-2">
                {[
                  'Web/Tarayıcı',
                  'Mobil (React Native)',
                  'Desktop (Electron)',
                  'PWA (Progressive Web App)',
                ].map((option) => (
                  <Button
                    key={option}
                    variant={answer === option ? 'default' : 'outline'}
                    onClick={() => setAnswer(option)}
                    className={`text-sm ${
                      answer === option
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}

            {field === 'features' && (
              <div className="grid grid-cols-2 gap-2">
                {[
                  'Kullanıcı girişi',
                  'Çok oyunculu',
                  'Sohbet sistemi',
                  'Ödeme/Mağaza',
                  'Başarım sistemi',
                  'Forum',
                  'Arkadaş sistemi',
                  'Bildirimler',
                ].map((option) => (
                  <Button
                    key={option}
                    variant={answer.includes(option) ? 'default' : 'outline'}
                    onClick={() => toggleMultiOption(option)}
                    className={`text-sm ${
                      answer.includes(option)
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'border-gray-600 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}

            {field === 'general' && (
              <Textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Cevabınızı yazın..."
                className="bg-gray-700 border-gray-600 text-white min-h-[80px]"
              />
            )}

            {answer && (
              <div className="mt-3 p-2 bg-gray-800 rounded text-sm text-green-400">
                <span className="font-medium">Seçiminiz: </span>
                {answer}
              </div>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                onOpenChange(false);
              }}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              İptal
            </Button>
            <Button
              onClick={onSubmit}
              className="bg-purple-600 hover:bg-purple-700"
              disabled={!answer.trim() || isLoading}
            >
              {isLoading && (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              )}
              Gönder
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
