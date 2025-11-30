import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Settings, Loader2 } from 'lucide-react';

export default function SettingsView({
  openaiKey,
  setOpenaiKey,
  isLoading,
  onSave,
}) {
  return (
    <div className="flex-1 overflow-auto p-8">
      <div className="max-w-2xl mx-auto">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-purple-400" />
              Ayarlar
            </CardTitle>
            <CardDescription className="text-gray-400">
              API anahtarlarınızı yönetin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSave} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  OpenAI API Key (Opsiyonel)
                </label>
                <Input
                  type="password"
                  placeholder="sk-..."
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="bg-gray-700 border-gray-600 text-white"
                />
                <p className="text-xs text-gray-400">
                  Kendi OpenAI API key&apos;inizi kullanmak isterseniz buraya
                  girin.
                </p>
              </div>
              <Button
                type="submit"
                className="bg-purple-600 hover:bg-purple-700"
                disabled={isLoading}
              >
                {isLoading && (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                )}
                Kaydet
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
