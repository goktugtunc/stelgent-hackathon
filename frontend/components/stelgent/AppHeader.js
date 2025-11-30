import { Button } from '@/components/ui/button';
import { Code2, FolderOpen, Settings, LogOut, Star } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function AppHeader({
  currentProject,
  user,
  onShowProjects,
  onShowSettings,
  onDisconnect,
}) {
  const router = useRouter();

  const goMintedProjects = () => {
    router.push('/minted-projects');
  };

  return (
    <header className="border-b border-gray-700 bg-gray-800 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Code2 className="h-5 w-5 text-purple-400" />
          <h1 className="text-lg font-bold">Stelgent</h1>
        </div>
        {currentProject && (
          <span className="text-sm text-gray-400">/ {currentProject.name}</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">
          {user?.stellar_public_key
            ? `${user.stellar_public_key.slice(0, 6)}...${user.stellar_public_key.slice(-4)}`
            : 'Wallet'}
        </span>

        {/* Projeler butonu */}
        <Button variant="ghost" size="sm" onClick={onShowProjects}>
          <FolderOpen className="h-4 w-4" />
        </Button>

        {/* Mint edilen projeler butonu */}
        <Button variant="ghost" size="sm" onClick={goMintedProjects}>
          <Star className="h-4 w-4 text-yellow-400" />
        </Button>

        {/* Ayarlar butonu */}
        <Button variant="ghost" size="sm" onClick={onShowSettings}>
          <Settings className="h-4 w-4" />
        </Button>

        {/* Çıkış */}
        <Button variant="ghost" size="sm" onClick={onDisconnect}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
