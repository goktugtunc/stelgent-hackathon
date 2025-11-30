import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export default function PreviewDialog({ open, onOpenChange, content }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gray-800 border-gray-700 text-white max-w-6xl w-[95vw] h-[90vh]">
        <DialogHeader>
          <DialogTitle className="text-green-400">Site Önizleme</DialogTitle>
          <DialogDescription className="text-gray-300">
            Oluşturulan sitenizin canlı önizlemesi
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden">
          <div className="h-[calc(90vh-120px)]">
            <iframe
              srcDoc={content}
              className="w-full h-full border-0 bg-white"
              sandbox="allow-scripts allow-same-origin"
              title="Site Önizleme"
            />
          </div>
        </div>
        <div className="flex justify-between items-center pt-4">
          <span className="text-sm text-gray-400">
            💡 İpucu: Dosyaları düzenledikten sonra &quot;Önizleme&quot; butonuna tekrar
            basın
          </span>
          <Button
            onClick={() => onOpenChange(false)}
            className="bg-gray-600 hover:bg-gray-700"
          >
            Kapat
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
