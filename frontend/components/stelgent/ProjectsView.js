import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Plus, FolderOpen, Trash2 } from 'lucide-react';

export default function ProjectsView({
  projects,
  newProjectName,
  setNewProjectName,
  isLoading,
  onCreateProject,
  onOpenProject,
  onDeleteProject,
}) {
  return (
    <div className="flex-1 overflow-auto p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-purple-400" />
              Yeni Proje
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Proje adı"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onCreateProject()}
                className="bg-gray-700 border-gray-600 text-white"
              />
              <Button
                onClick={onCreateProject}
                className="bg-purple-600 hover:bg-purple-700"
                disabled={isLoading}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-purple-400" />
              Projelerim
            </CardTitle>
          </CardHeader>
          <CardContent>
            {projects.length === 0 ? (
              <p className="text-gray-400 text-center py-8">
                Henüz proje oluşturmadınız.
              </p>
            ) : (
              <div className="space-y-3">
                {projects.map((project) => (
                  <Card
                    key={project.id}
                    className="bg-gray-700 border-gray-600"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-white">
                            {project.name}
                          </h3>
                          <p className="text-sm text-gray-400">
                            {new Date(
                              project.created_at
                            ).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => onOpenProject(project)}
                            className="bg-purple-600 hover:bg-purple-700"
                          >
                            Aç
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => onDeleteProject(project.id)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
