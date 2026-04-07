
import { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/Sidebar";
import NoteEditor from "../components/NoteEditor";
import { Button } from "../components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "../components/ui/sheet";
import { Menu, Plus } from "lucide-react";

const Dashboard = () => {
  const { user, logout, setUserData } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [folders, setFolders] = useState([]);
  const [notes, setNotes] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [selectedNote, setSelectedNote] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Set user from location state if available
  useEffect(() => {
    if (location.state?.user && !user) {
      setUserData(location.state.user);
    }
  }, [location.state, user, setUserData]);

  const currentUser = user || location.state?.user;
  const userId = currentUser?.user_id;

  // Load folders and notes from MongoDB API
  useEffect(() => {
    if (!userId) return;

    setIsLoading(true);

    // Load folders from API
    const loadFolders = async () => {
      try {
        const response = await fetch("/api/folders", {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setFolders(data.folders || []);
        } else {
          setFolders([]);
        }
      } catch (error) {
        console.error("Folders loading error:", error);
        setFolders([]);
      }
    };

    // Load notes from API
    const loadNotes = async () => {
      try {
        const response = await fetch("/api/notes", {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setNotes(data.notes || []);
        } else {
          console.error("Failed to load notes");
          setNotes([]);
        }
        setIsLoading(false);
      } catch (error) {
        console.error("Notes loading error:", error);
        setNotes([]);
        setIsLoading(false);
      }
    };

    loadFolders();
    loadNotes();

    // Polling to refresh data every 30 seconds
    const intervalId = setInterval(() => {
      loadFolders();
      loadNotes();
    }, 30000);

    return () => clearInterval(intervalId);
  }, [userId]);

  // Filter notes based on folder and search
  const filteredNotes = notes.filter(note => {
    const matchesFolder = !selectedFolder || note.folder_id === selectedFolder;
    const matchesSearch = !searchQuery ||
      note.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFolder && matchesSearch;
  });

  // Create new note
  const handleCreateNote = async () => {
    try {
      const response = await fetch("/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          title: "Untitled Note",
          content: "",
          folder_id: selectedFolder,
          is_shared: false
        })
      });

      if (!response.ok) throw new Error("Failed to create note");

      const newNote = await response.json();
      // Add the new note to the local state immediately
      setNotes(prev => [...prev, newNote]);
      setSelectedNote(newNote);
      setIsMobileSidebarOpen(false);
      toast.success("Note created");
    } catch (error) {
      console.error("Create note error:", error);
      toast.error("Failed to create note");
    }
  };

  // Update note
  const handleUpdateNote = async (noteId, data) => {
    try {
      const response = await fetch(`/api/notes/${noteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(data)
      });

      if (!response.ok) throw new Error("Failed to update note");

      const updatedNote = await response.json();
      setSelectedNote(updatedNote);
    } catch (error) {
      console.error("Update note error:", error);
      toast.error("Failed to save note");
    }
  };

  // Delete note
  const handleDeleteNote = async (noteId) => {
    try {
      const response = await fetch(`/api/notes/${noteId}`, {
        method: "DELETE",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to delete note");

      // Remove the note from local state immediately
      setNotes(prev => prev.filter(note => note.note_id !== noteId));
      
      if (selectedNote?.note_id === noteId) {
        setSelectedNote(null);
      }
      toast.success("Note deleted");
    } catch (error) {
      console.error("Delete note error:", error);
      toast.error("Failed to delete note");
    }
  };

  // Share note
  const handleShareNote = async (noteId) => {
    try {
      const response = await fetch(`/api/notes/${noteId}/share`, {
        method: "POST",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to share note");

      const data = await response.json();
      console.log("Share response data:", data);
      const shareUrl = `${window.location.origin}/shared/${data.share_link}`;
      console.log("Generated share URL:", shareUrl);

      await navigator.clipboard.writeText(shareUrl);
      toast.success("Share link copied to clipboard!");
    } catch (error) {
      console.error("Share note error:", error);
      toast.error("Failed to share note");
    }
  };

  // Create folder
  const handleCreateFolder = async (name, color) => {
    try {
      const response = await fetch("/api/folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name, color })
      });

      if (!response.ok) throw new Error("Failed to create folder");

      const newFolder = await response.json();
      // Add the new folder to the local state immediately
      setFolders(prev => [...prev, newFolder]);
      toast.success("Folder created");
    } catch (error) {
      console.error("Create folder error:", error);
      toast.error("Failed to create folder");
    }
  };

  // Delete folder
  const handleDeleteFolder = async (folderId) => {
    try {
      const response = await fetch(`/api/folders/${folderId}`, {
        method: "DELETE",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to delete folder");

      // Remove the folder from local state immediately
      setFolders(prev => prev.filter(folder => folder.folder_id !== folderId));
      
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
      }
      toast.success("Folder deleted");
    } catch (error) {
      console.error("Delete folder error:", error);
      toast.error("Failed to delete folder");
    }
  };

  // Logout
  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#FDF8F5] to-[#F4F0EB]">
        <div className="text-center">
          <div className="relative mx-auto mb-6">
            <div className="animate-ping absolute inset-0 rounded-full bg-[#E06A4F]/20 h-12 w-12"></div>
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-[#E7E5E4] border-t-[#E06A4F] mx-auto"></div>
          </div>
          <p className="text-lg font-heading font-medium text-[#1C1917]">Loading your notes</p>
          <p className="text-sm text-[#A8A29E] font-body mt-1">Almost there...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-[#FDF8F5] to-[#F4F0EB] overflow-hidden" data-testid="dashboard">
      {/* Desktop Sidebar */}
      <div className="hidden md:block w-80 lg:w-85 flex-shrink-0">
        <div className="h-full bg-white/70 backdrop-blur-xl border-r border-[#E7E5E4]/50 shadow-xl shadow-[#E7E5E4]/10">
          <Sidebar
          user={currentUser}
          folders={folders}
          notes={filteredNotes}
          selectedFolder={selectedFolder}
          selectedNote={selectedNote}
          searchQuery={searchQuery}
          onSelectFolder={setSelectedFolder}
          onSelectNote={(note) => {
            setSelectedNote(note);
            setIsMobileSidebarOpen(false);
          }}
          onSearchChange={setSearchQuery}
          onCreateNote={handleCreateNote}
          onCreateFolder={handleCreateFolder}
          onDeleteFolder={handleDeleteFolder}
          onLogout={handleLogout}
        />
        </div>
      </div>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-b border-[#E7E5E4]/60 px-4 py-3 flex items-center justify-between shadow-lg shadow-[#E7E5E4]/20">
        <Sheet open={isMobileSidebarOpen} onOpenChange={setIsMobileSidebarOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" data-testid="mobile-menu-button">
              <Menu className="h-5 w-5 text-[#1C1917]" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 w-80 bg-gradient-to-br from-[#FDF8F5] to-[#F4F0EB]">
            <Sidebar
              user={currentUser}
              folders={folders}
              notes={filteredNotes}
              selectedFolder={selectedFolder}
              selectedNote={selectedNote}
              searchQuery={searchQuery}
              onSelectFolder={setSelectedFolder}
              onSelectNote={(note) => {
                setSelectedNote(note);
                setIsMobileSidebarOpen(false);
              }}
              onSearchChange={setSearchQuery}
              onCreateNote={handleCreateNote}
              onCreateFolder={handleCreateFolder}
              onDeleteFolder={handleDeleteFolder}
              onLogout={handleLogout}
            />
          </SheetContent>
        </Sheet>

        <h1 className="font-heading font-semibold text-[#1C1917]">
          {selectedNote?.title || "Xero Notes"}
        </h1>

        <Button
          variant="ghost"
          size="icon"
          onClick={handleCreateNote}
          data-testid="mobile-new-note-button"
        >
          <Plus className="h-5 w-5 text-[#E06A4F]" />
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col md:pt-0 pt-14 overflow-hidden">
        {selectedNote ? (
          <div className="flex-1 m-3 lg:m-5 mb-0 rounded-2xl overflow-hidden shadow-2xl shadow-[#E7E5E4]/30 bg-white/90 backdrop-blur-sm border border-[#E7E5E4]/50">
            <NoteEditor
            note={selectedNote}
            folders={folders}
            onUpdate={handleUpdateNote}
            onDelete={handleDeleteNote}
            onShare={handleShareNote}
          />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
            <div className="text-center max-w-md">
              <div className="relative mb-8">
                <div className="absolute inset-0 bg-gradient-to-br from-[#E06A4F]/15 to-[#F59E0B]/10 rounded-3xl blur-2xl transform rotate-6"></div>
                <img
                  src="https://images.unsplash.com/photo-1759296844873-e0c694c24284?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwzfHxtaW5pbWFsaXN0JTIwY2xlYW4lMjBkZXNrJTIwd29ya3NwYWNlJTIwYnJpZ2h0fGVufDB8fHx8MTc3NDUzNjU0MXww&ixlib=rb-4.1.0&q=85"
                  alt="Empty state"
                  className="w-48 h-48 sm:w-56 sm:h-56 object-cover rounded-3xl mx-auto mb-6 shadow-2xl shadow-[#E7E5E4]/40 relative z-10 ring-1 ring-[#E7E5E4]/50"
                />
              </div>
              <h2 className="font-heading text-2xl sm:text-3xl font-semibold text-[#1C1917] mb-3 tracking-tight">
                No note selected
              </h2>
              <p className="text-[#78716C] font-body mb-8 text-base sm:text-lg leading-relaxed">
                Select a note from the sidebar or create a new one<br className="hidden sm:inline" />to get started
              </p>
              <Button
                onClick={handleCreateNote}
                className="bg-gradient-to-r from-[#E06A4F] to-[#C95A41] hover:from-[#C95A41] hover:to-[#E06A4F] text-white rounded-full px-8 py-6 text-base font-medium shadow-lg shadow-[#E06A4F]/25 transition-all duration-300 hover:shadow-xl hover:shadow-[#E06A4F]/35 hover:-translate-y-0.5 ring-1 ring-white/50"
                data-testid="create-first-note-button"
              >
                <Plus className="h-5 w-5 mr-2" />
                Create your first note
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
