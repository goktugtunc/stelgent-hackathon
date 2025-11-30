import dynamic from 'next/dynamic';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Loader2, Send, Code2 } from 'lucide-react';
import FileTree from '@/components/FileTree';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
});

export default function EditorView({
  projects = [], // <-- default boş array
  currentProject,
  files,
  selectedFile,
  onSelectFile,
  editorContent,
  onEditorChange,
  onSaveFile,
  onDeploy,
  onStopContainer,
  onOpenContainer,
  containerStatus,
  isDeploying,
  conversations,
  chatMessage,
  setChatMessage,
  isLoading,
  onSendMessage,
  onFileCreate,
  onFileDelete,
  onFileRename,
  onGeneratePreview,
  getLanguageFromFilename,
  // IPFS + Mint props
  onExportToIpfs,
  onExportAndMint,
  isExportingIpfs = false,
  isExportingAndMinting = false,
}) {
  return (
    <div className="flex-1 overflow-hidden">
      <ResizablePanelGroup direction="horizontal">
        {/* Chat */}
        <ResizablePanel defaultSize={30} minSize={20}>
          <div className="h-full flex flex-col bg-gray-800">
            <div className="p-3 border-b border-gray-700">
              <h2 className="font-semibold text-sm">AI Assistant</h2>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {conversations.length === 0 && (
                <div className="text-center text-gray-400 text-sm py-8">
                  AI ile konuşarak kod üretin.
                  <br />
                  Örnek: &quot;Bir login formu oluştur&quot;
                </div>
              )}
              {conversations.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-purple-600 ml-8'
                      : 'bg-gray-700 mr-8'
                  }`}
                >
                  <div className="text-xs text-gray-300 mb-1">
                    {msg.role === 'user' ? 'Sen' : 'AI'}
                  </div>
                  <div className="text-sm whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="bg-gray-700 mr-8 p-3 rounded-lg flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-xs text-gray-300">
                    AI cevap oluşturuyor...
                  </span>
                </div>
              )}
            </div>
            <form
              onSubmit={onSendMessage}
              data-chat-form
              className="p-3 border-t border-gray-700"
            >
              <div className="flex gap-2">
                <Input
                  placeholder="Mesajınızı yazın..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  className="bg-gray-700 border-gray-600 text-white"
                  disabled={isLoading}
                />
                <Button type="submit" size="icon" disabled={isLoading}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* FileTree + Editor */}
        <ResizablePanel defaultSize={70}>
          <ResizablePanelGroup direction="horizontal">
            <ResizablePanel defaultSize={20} minSize={15}>
              <FileTree
                files={files}
                onFileSelect={onSelectFile}
                onFileCreate={onFileCreate}
                onFileDelete={onFileDelete}
                onFileRename={onFileRename}
                selectedFile={selectedFile}
              />
            </ResizablePanel>

            <ResizableHandle />

            <ResizablePanel defaultSize={80}>
              <div className="h-full flex flex-col bg-gray-900">
                {selectedFile ? (
                  <>
                    <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between bg-gray-800">
                      <span className="text-sm text-gray-300">
                        {selectedFile.path}
                      </span>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={onGeneratePreview}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Önizleme
                        </Button>

                        {/* IPFS + Mint Buttons */}
                        <Button
                          size="sm"
                          onClick={() =>
                            onExportToIpfs && onExportToIpfs()
                          }
                          className="bg-teal-600 hover:bg-teal-700"
                          disabled={
                            isExportingIpfs ||
                            isExportingAndMinting ||
                            files.length === 0
                          }
                        >
                          {isExportingIpfs ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            'IPFS’e Yükle'
                          )}
                        </Button>

                        <Button
                          size="sm"
                          onClick={() =>
                            onExportAndMint && onExportAndMint()
                          }
                          className="bg-indigo-600 hover:bg-indigo-700"
                          disabled={
                            isExportingAndMinting ||
                            isExportingIpfs ||
                            files.length === 0
                          }
                        >
                          {isExportingAndMinting ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            'IPFS’e Yükle + Mint Et'
                          )}
                        </Button>

                        {containerStatus.deployed &&
                        containerStatus.status === 'running' ? (
                          <>
                            <Button
                              size="sm"
                              onClick={onOpenContainer}
                              className="bg-blue-600 hover:bg-blue-700"
                              disabled={isDeploying}
                            >
                              🌐 Aç
                            </Button>
                            <Button
                              size="sm"
                              onClick={onStopContainer}
                              className="bg-red-600 hover:bg-red-700"
                              disabled={isDeploying}
                            >
                              {isDeploying ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                '⏹️ Durdur'
                              )}
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="sm"
                            onClick={onDeploy}
                            className="bg-orange-600 hover:bg-orange-700"
                            disabled={isDeploying || files.length === 0}
                          >
                            {isDeploying ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              '🚀 Deploy'
                            )}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          onClick={onSaveFile}
                          className="bg-purple-600 hover:bg-purple-700"
                        >
                          Kaydet
                        </Button>
                      </div>
                    </div>
                    <div className="flex-1">
                      <MonacoEditor
                        height="100%"
                        language={getLanguageFromFilename(selectedFile.path)}
                        theme="vs-dark"
                        value={editorContent}
                        onChange={onEditorChange}
                        options={{
                          minimap: { enabled: false },
                          fontSize: 14,
                          lineNumbers: 'on',
                          scrollBeyondLastLine: false,
                          automaticLayout: true,
                        }}
                      />
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    <div className="text-center">
                      <Code2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Bir dosya seçin veya AI ile oluşturun</p>
                    </div>
                  </div>
                )}
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
