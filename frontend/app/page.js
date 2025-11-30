'use client';

import { useState, useEffect } from 'react';
import {
  isConnected,
  isAllowed,
  setAllowed,
  requestAccess,
} from '@stellar/freighter-api';
import { useToast } from '@/components/ui/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { apiGet, apiPost, apiPut, apiDelete } from '../lib/api';

import AppHeader from '@/components/stelgent/AppHeader';
import HomeView from '@/components/stelgent/HomeView';
import ProjectsView from '@/components/stelgent/ProjectsView';
import EditorView from '@/components/stelgent/EditorView';
import SettingsView from '@/components/stelgent/SettingsView';
import ClarificationDialog from '@/components/stelgent/ClarificationDialog';
import PreviewDialog from '@/components/stelgent/PreviewDialog';

export default function App() {
  const { toast } = useToast();

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState('home'); // 'home' | 'projects' | 'editor' | 'settings'
  const [isLoading, setIsLoading] = useState(false);

  // Wallet
  const [isWalletConnected, setIsWalletConnected] = useState(false);
  const [stellarPublicKey, setStellarPublicKey] = useState('');
  const [isConnectingWallet, setIsConnectingWallet] = useState(false);

  // Projects
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);

  // Files / editor
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [editorContent, setEditorContent] = useState('');

  // Chat
  const [conversations, setConversations] = useState([]);
  const [chatMessage, setChatMessage] = useState('');
  const [newProjectName, setNewProjectName] = useState('');

  // Clarification modal
  const [showClarificationModal, setShowClarificationModal] = useState(false);
  const [clarificationQuestion, setClarificationQuestion] = useState('');
  const [clarificationField, setClarificationField] = useState('');
  const [clarificationAnswer, setClarificationAnswer] = useState('');

  // Preview
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState('');

  // Container
  const [containerStatus, setContainerStatus] = useState({
    deployed: false,
    status: 'not_deployed',
    url: undefined,
    port: undefined,
  });
  const [isDeploying, setIsDeploying] = useState(false);

  // Settings
  const [openaiKey, setOpenaiKey] = useState('');

  // IPFS export / mint
  const [isExportingIpfs, setIsExportingIpfs] = useState(false);
  const [isExportingAndMinting, setIsExportingAndMinting] = useState(false);


  // ========== INIT ==========

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('token');
    if (token) {
      // Token = Stellar public key
      setStellarPublicKey(token);
      setIsWalletConnected(true);
      fetchUserData();
    }
  }, []);

  useEffect(() => {
    if (currentProject) {
      fetchFiles();
      fetchConversations();
      fetchContainerStatus();
    }
  }, [currentProject]);

  useEffect(() => {
    if (selectedFile) {
      setEditorContent(selectedFile.content || '');
    }
  }, [selectedFile]);

  // ========== WALLET ==========

  const connectWallet = async () => {
    setIsConnectingWallet(true);
    try {
      if (typeof window === 'undefined') {
        throw new Error('Bu işlem sadece tarayıcıda mümkündür.');
      }

      const connRes = await isConnected();
      if (connRes.error) console.error('isConnected error:', connRes.error);
      if (!connRes.isConnected) {
        throw new Error('Freighter yüklü değil. Lütfen tarayıcınıza yükleyin.');
      }

      const allowedRes = await isAllowed();
      if (allowedRes.error) console.error('isAllowed error:', allowedRes.error);

      if (!allowedRes.isAllowed) {
        const setAllowedRes = await setAllowed();
        if (setAllowedRes.error) {
          throw new Error('Kullanıcı izni alınamadı.');
        }
        if (!setAllowedRes.isAllowed) {
          throw new Error('Kullanıcı uygulamaya izin vermedi.');
        }
      }

      const accessRes = await requestAccess();
      if (accessRes.error) {
        throw new Error(accessRes.error);
      }
      const publicKey = accessRes.address;
      if (!publicKey) {
        throw new Error('Public key alınamadı.');
      }

      // Backend’e sadece kayıt/lookup için gidiyoruz
      const response = await apiPost('/api/auth/wallet/connect', {
        public_key: publicKey,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Wallet login başarısız.');
      }

      if (typeof window !== 'undefined') {
        // TOKEN = PUBLIC KEY
        localStorage.setItem('token', publicKey);
      }

      setUser(data.user);
      setIsLoggedIn(true);
      setActiveView('projects');
      setStellarPublicKey(publicKey);
      setIsWalletConnected(true);
      await fetchProjects();

      toast({ title: 'Başarılı!', description: 'Wallet ile giriş yapıldı.' });
    } catch (err) {
      console.error('connectWallet error:', err);
      toast({
        title: 'Hata',
        description: err?.message || 'Wallet bağlantısı başarısız.',
        variant: 'destructive',
      });
    } finally {
      setIsConnectingWallet(false);
    }
  };

  const disconnectWallet = () => {
    setStellarPublicKey('');
    setIsWalletConnected(false);
    setUser(null);
    setIsLoggedIn(false);
    setActiveView('home');
    setProjects([]);
    setCurrentProject(null);
    setFiles([]);
    setSelectedFile(null);
    setOpenaiKey('');
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    toast({ title: 'Başarılı!', description: 'Wallet bağlantısı kesildi.' });
  };

  // ========== API KATLARI ==========

  const fetchUserData = async () => {
    try {
      const response = await apiGet('/api/auth/me');
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setIsLoggedIn(true);
        setActiveView('projects');
        setOpenaiKey(data.user.openai_api_key || '');
        setStellarPublicKey(data.user.stellar_public_key || '');
        setIsWalletConnected(true);
        await fetchProjects();
      } else {
        if (typeof window !== 'undefined') localStorage.removeItem('token');
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      if (typeof window !== 'undefined') localStorage.removeItem('token');
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await apiGet('/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  const fetchFiles = async () => {
    if (!currentProject) return;
    try {
      const response = await apiGet(`/api/projects/${currentProject.id}/files`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files);
      }
    } catch (error) {
      console.error('Failed to fetch files:', error);
    }
  };

  const fetchConversations = async () => {
    if (!currentProject) return;
    try {
      const response = await apiGet(
        `/api/projects/${currentProject.id}/conversations`
      );
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const fetchContainerStatus = async () => {
    if (!currentProject) return;
    try {
      const response = await apiGet(
        `/api/projects/${currentProject.id}/container-status`
      );
      if (response.ok) {
        const data = await response.json();
        setContainerStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch container status:', error);
    }
  };

  const handleExportToIpfs = async () => {
    if (!currentProject) {
      toast({
        title: 'Uyarı',
        description: 'Önce bir proje seçin.',
        variant: 'destructive',
      });
      return;
    }
  
    // Stellar public key'i localStorage'dan çek
    const stellarAddress =
      typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
    if (!stellarAddress) {
      toast({
        title: 'Cüzdan yok',
        description: 'Lütfen önce Stellar cüzdanını bağlayın.',
        variant: 'destructive',
      });
      return;
    }
  
    setIsExportingIpfs(true);
    try {
      const response = await apiPost(
        `/api/projects/${currentProject.id}/export-ipfs`,
        {
          stellar_address: stellarAddress, // backend buradan alacak
        }
      );
      const data = await response.json();
    
      if (response.ok) {
        toast({
          title: 'IPFS’e yüklendi',
          description: `CID: ${
            data.ipfs_cid || data.cid || 'CID bilgisi döndürülmedi.'
          }`,
        });
      } else {
        toast({
          title: 'Hata',
          description:
            data.detail || data.error || 'IPFS yükleme işlemi başarısız.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('IPFS export error:', error);
      toast({
        title: 'Hata',
        description: 'IPFS yükleme sırasında hata oluştu.',
        variant: 'destructive',
      });
    } finally {
      setIsExportingIpfs(false);
    }
  };
  
  const handleExportAndMint = async () => {
    if (!currentProject) {
      toast({
        title: 'Uyarı',
        description: 'Önce bir proje seçin.',
        variant: 'destructive',
      });
      return;
    }
  
    const stellarAddress =
      typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
    if (!stellarAddress) {
      toast({
        title: 'Cüzdan yok',
        description: 'Lütfen önce Stellar cüzdanını bağlayın.',
        variant: 'destructive',
      });
      return;
    }
  
    setIsExportingAndMinting(true);
    try {
      const response = await apiPost(
        `/api/projects/${currentProject.id}/export-ipfs`,
        {
          stellar_address: stellarAddress,
        }
      );
      const data = await response.json();
    
      if (response.ok) {
        toast({
          title: 'IPFS’e yüklendi + NFT mint edildi',
          description: `CID: ${
            data.ipfs_cid || data.cid || 'CID bilgisi döndürülmedi.'
          }`,
        });
      } else {
        toast({
          title: 'Hata',
          description:
            data.detail ||
            data.error ||
            'IPFS + mint işlemi tamamlanamadı.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Export & mint error:', error);
      toast({
        title: 'Hata',
        description: 'IPFS + mint işlemi sırasında hata oluştu.',
        variant: 'destructive',
      });
    } finally {
      setIsExportingAndMinting(false);
    }
  };

  const deployProject = async () => {
    if (!currentProject) return;
    setIsDeploying(true);
    try {
      const response = await apiPost(
        `/api/projects/${currentProject.id}/deploy`,
        {}
      );
      const data = await response.json();

      if (response.ok) {
        toast({
          title: 'Başarılı!',
          description: `Proje başarıyla deploy edildi. Port: ${data.port}`,
        });
        fetchContainerStatus();
        if (typeof window !== 'undefined') {
          window.open(data.container_url, '_blank');
        }
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Deploy işlemi başarısız.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Deploy failed:', error);
      toast({
        title: 'Hata',
        description: 'Deploy işlemi sırasında hata oluştu.',
        variant: 'destructive',
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const stopContainer = async () => {
    if (!currentProject) return;
    setIsDeploying(true);
    try {
      const response = await apiDelete(
        `/api/projects/${currentProject.id}/deploy`
      );
      const data = await response.json();
      if (response.ok) {
        toast({ title: 'Başarılı!', description: 'Container durduruldu.' });
        fetchContainerStatus();
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Container durdurulamadı.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Stop container failed:', error);
      toast({
        title: 'Hata',
        description: 'Container durdurma sırasında hata oluştu.',
        variant: 'destructive',
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const openContainer = () => {
    if (containerStatus.url && typeof window !== 'undefined') {
      window.open(containerStatus.url, '_blank');
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName) return;
    setIsLoading(true);

    try {
      const response = await apiPost('/api/projects', {
        name: newProjectName,
      });
      const data = await response.json();

      if (response.ok) {
        toast({ title: 'Başarılı!', description: 'Proje oluşturuldu.' });
        fetchProjects();
        setNewProjectName('');
        setCurrentProject(data.project);
        setActiveView('editor');
      } else {
        toast({
          title: 'Hata',
          description: data.error || 'Proje oluşturulamadı.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Proje oluşturulamadı.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenProject = (project) => {
    setCurrentProject(project);
    setActiveView('editor');
  };

  const handleDeleteProject = async (projectId) => {
    try {
      const response = await apiDelete(`/api/projects/${projectId}`);
      const data = await response.json();

      if (response.ok) {
        toast({ title: 'Başarılı', description: 'Proje silindi.' });
        fetchProjects();
        if (currentProject?.id === projectId) {
          setCurrentProject(null);
          setActiveView('projects');
        }
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Proje silinemedi.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Delete project failed:', error);
      toast({
        title: 'Hata',
        description: 'Proje silinemedi.',
        variant: 'destructive',
      });
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || !currentProject) return;

    setIsLoading(true);
    const userMessage = chatMessage;
    setChatMessage('');

    setConversations((prev) => [
      ...prev,
      { role: 'user', content: userMessage, created_at: new Date() },
    ]);

    try {
      const response = await apiPost(
        `/api/projects/${currentProject.id}/chat`,
        { message: userMessage }
      );
      const data = await response.json();

      if (response.ok) {
        if (data.message === 'clarification_requested') {
          setClarificationQuestion(data.question);
          setClarificationField(data.field);
          setShowClarificationModal(true);
          setConversations((prev) => prev.slice(0, -1));
        } else {
          setConversations((prev) => [
            ...prev,
            { role: 'assistant', content: data.response, created_at: new Date() },
          ]);
          toast({ title: 'Başarılı!', description: 'Kod oluşturuldu.' });
          fetchFiles();
        }
      } else {
        toast({
          title: 'Hata',
          description: data.error || 'Mesaj gönderilemedi.',
          variant: 'destructive',
        });
        setConversations((prev) => prev.slice(0, -1));
      }
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Mesaj gönderilemedi.',
        variant: 'destructive',
      });
      setConversations((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileCreate = async (path, type) => {
    if (!currentProject) return;
    try {
      const response = await apiPost(
        `/api/projects/${currentProject.id}/files`,
        { path, type, content: '' }
      );

      if (response.ok) {
        toast({
          title: 'Başarılı',
          description: `${type === 'folder' ? 'Klasör' : 'Dosya'} oluşturuldu.`,
        });
        fetchFiles();
      } else {
        const data = await response.json();
        toast({
          title: 'Hata',
          description: data.error || 'Oluşturulamadı.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Oluşturulamadı.',
        variant: 'destructive',
      });
    }
  };

  const handleFileDelete = async (fileId) => {
    if (!currentProject) return;
    try {
      const response = await apiDelete(
        `/api/projects/${currentProject.id}/files/${fileId}`
      );
      const data = await response.json();

      if (response.ok) {
        toast({ title: 'Başarılı', description: 'Silindi.' });
        fetchFiles();
        if (selectedFile?.id === fileId) {
          setSelectedFile(null);
        }
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Silinemedi.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Delete file failed:', error);
      toast({
        title: 'Hata',
        description: 'Silinemedi.',
        variant: 'destructive',
      });
    }
  };

  const handleFileRename = async (fileId, newPath) => {
    if (!currentProject) return;
    try {
      const response = await apiPut(
        `/api/projects/${currentProject.id}/files/${fileId}`,
        { path: newPath }
      );
      const data = await response.json();

      if (response.ok) {
        toast({ title: 'Başarılı', description: 'Yeniden adlandırıldı.' });
        fetchFiles();
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Yeniden adlandırılamadı.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Rename file failed:', error);
      toast({
        title: 'Hata',
        description: 'Yeniden adlandırılamadı.',
        variant: 'destructive',
      });
    }
  };

  const handleEditorChange = (value) => {
    setEditorContent(value || '');
  };

  const handleSaveFile = async () => {
    if (!selectedFile || !currentProject) return;

    try {
      const response = await apiPut(
        `/api/projects/${currentProject.id}/files/${selectedFile.id}`,
        { content: editorContent }
      );
      const data = await response.json();

      if (response.ok) {
        toast({ title: 'Başarılı', description: 'Dosya kaydedildi.' });
        setFiles((prev) =>
          prev.map((f) =>
            f.id === selectedFile.id ? { ...f, content: editorContent } : f
          )
        );
        setSelectedFile({ ...selectedFile, content: editorContent });
      } else {
        toast({
          title: 'Hata',
          description: data.detail || 'Dosya kaydedilemedi.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Save file failed:', error);
      toast({
        title: 'Hata',
        description: 'Dosya kaydedilemedi.',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateOpenAI = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await apiPost('/api/settings/openai', {
        openai_api_key: openaiKey,
      });

      if (response.ok) {
        toast({
          title: 'Başarılı!',
          description: 'OpenAI API key güncellendi.',
        });
      } else {
        toast({
          title: 'Hata',
          description: 'Güncellenemedi.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Bir hata oluştu.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getLanguageFromFilename = (filename) => {
    const ext = filename.split('.').pop();
    const languageMap = {
      js: 'javascript',
      jsx: 'javascript',
      ts: 'typescript',
      tsx: 'typescript',
      py: 'python',
      html: 'html',
      css: 'css',
      json: 'json',
      md: 'markdown',
      txt: 'plaintext',
    };
    return languageMap[ext] || 'plaintext';
  };

  const generatePreview = () => {
    const htmlFile =
      files.find((f) => f.path === 'index.html') ||
      files.find((f) => f.path.endsWith('.html'));
    if (!htmlFile) {
      toast({
        title: 'Uyarı',
        description: 'HTML dosyası bulunamadı.',
        variant: 'destructive',
      });
      return;
    }

    let htmlContent = htmlFile.content || '';

    const cssFiles = files.filter((f) => f.path.endsWith('.css'));
    let cssContent = '';
    cssFiles.forEach((cssFile) => {
      cssContent += `\n/* ${cssFile.path} */\n${cssFile.content || ''}\n`;
    });

    const jsFiles = files.filter(
      (f) => f.path.endsWith('.js') && !f.path.includes('node_modules')
    );
    let jsContent = '';
    jsFiles.forEach((jsFile) => {
      jsContent += `\n/* ${jsFile.path} */\n${jsFile.content || ''}\n`;
    });

    if (!htmlContent.includes('<html')) {
      htmlContent = `<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Önizleme</title>
</head>
<body>
${htmlContent}
</body>
</html>`;
    }

    if (cssContent.trim()) {
      const styleTag = `\n<style>${cssContent}</style>\n`;
      if (htmlContent.includes('</head>')) {
        htmlContent = htmlContent.replace('</head>', styleTag + '</head>');
      } else {
        htmlContent = htmlContent.replace('<head>', '<head>' + styleTag);
      }
    }

    if (jsContent.trim()) {
      const scriptTag = `\n<script>${jsContent}</script>\n`;
      if (htmlContent.includes('</body>')) {
        htmlContent = htmlContent.replace('</body>', scriptTag + '</body>');
      } else {
        htmlContent = htmlContent + scriptTag;
      }
    }

    const baseStyles = `
    <style>
      body { 
        margin: 0; 
        padding: 20px; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
        line-height: 1.6; 
      }
      * { 
        box-sizing: border-box; 
      }
      img { 
        max-width: 100%; 
        height: auto; 
      }
      .container {
        max-width: 1200px;
        margin: 0 auto;
      }
    </style>`;

    if (htmlContent.includes('</head>')) {
      htmlContent = htmlContent.replace('</head>', baseStyles + '\n</head>');
    } else {
      htmlContent = htmlContent.replace('<head>', '<head>' + baseStyles);
    }

    setPreviewContent(htmlContent);
    setShowPreview(true);
  };

  const handleClarificationSubmit = async () => {
    if (!clarificationAnswer.trim()) return;

    const answer = clarificationAnswer;
    setClarificationAnswer('');
    setShowClarificationModal(false);

    setConversations((prev) => [
      ...prev,
      { role: 'assistant', content: clarificationQuestion, created_at: new Date() },
      { role: 'user', content: answer, created_at: new Date() },
    ]);

    setChatMessage(answer);

    setTimeout(() => {
      if (typeof document !== 'undefined') {
        const form = document.querySelector('form[data-chat-form]');
        if (form) form.requestSubmit();
      }
    }, 100);
  };

  // ========== RENDER ==========

  if (!isLoggedIn && activeView === 'home') {
    return (
      <>
        <HomeView
          isConnectingWallet={isConnectingWallet}
          onConnectWallet={connectWallet}
        />
        <Toaster />
      </>
    );
  }

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col">
      <AppHeader
        currentProject={currentProject}
        user={user}
        onShowProjects={() => setActiveView('projects')}
        onShowSettings={() => setActiveView('settings')}
        onDisconnect={disconnectWallet}
      />

      {activeView === 'projects' && (
        <ProjectsView
          projects={projects}
          newProjectName={newProjectName}
          setNewProjectName={setNewProjectName}
          isLoading={isLoading}
          onCreateProject={handleCreateProject}
          onOpenProject={handleOpenProject}
          onDeleteProject={handleDeleteProject}
        />
      )}

            {activeView === 'editor' && currentProject && (
        <EditorView
          currentProject={currentProject}
          files={files}
          selectedFile={selectedFile}
          onSelectFile={setSelectedFile}
          editorContent={editorContent}
          onEditorChange={handleEditorChange}
          onSaveFile={handleSaveFile}
          onDeploy={deployProject}
          onStopContainer={stopContainer}
          onOpenContainer={openContainer}
          containerStatus={containerStatus}
          isDeploying={isDeploying}
          conversations={conversations}
          chatMessage={chatMessage}
          setChatMessage={setChatMessage}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          onFileCreate={handleFileCreate}
          onFileDelete={handleFileDelete}
          onFileRename={handleFileRename}
          onGeneratePreview={generatePreview}
          getLanguageFromFilename={getLanguageFromFilename}
          onExportToIpfs={handleExportToIpfs}
          onExportAndMint={handleExportAndMint}
          isExportingIpfs={isExportingIpfs}
          isExportingAndMinting={isExportingAndMinting}
        />
      )}

      {activeView === 'settings' && (
        <SettingsView
          openaiKey={openaiKey}
          setOpenaiKey={setOpenaiKey}
          isLoading={isLoading}
          onSave={handleUpdateOpenAI}
        />
      )}

      <ClarificationDialog
        open={showClarificationModal}
        onOpenChange={setShowClarificationModal}
        question={clarificationQuestion}
        field={clarificationField}
        answer={clarificationAnswer}
        setAnswer={setClarificationAnswer}
        isLoading={isLoading}
        onSubmit={handleClarificationSubmit}
      />

      <PreviewDialog
        open={showPreview}
        onOpenChange={setShowPreview}
        content={previewContent}
      />

      <Toaster />
    </div>
  );
}
