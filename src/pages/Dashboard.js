
import { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { collection, onSnapshot, query, where, orderBy } from "firebase/firestore";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { API } from "../App";
import Sidebar from "../components/Sidebar";
import NoteEditor from "../components/NoteEditor";
import { Button } from "../components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "../components/ui/sheet";
import { Menu, Plus } from "lucide-react";

const Dashboard = ({ firestoreDb }) => {
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

  // Real-time Firestore listeners
  useEffect(() => {
    if (!userId) return;

    setIsLoading(true);

    // Folders listener
    const foldersQuery = query(
      collection(firestoreDb, "folders"),
      where("user_id", "==", userId)
    );

    const unsubFolders = onSnapshot(foldersQuery, (snapshot) => {
      const foldersData = snapshot.docs.map(doc => doc.data());
      setFolders(foldersData);
    }, (error) => {
      console.error("Folders listener error:", error);
    });

    // Notes listener - use MongoDB API instead of Firebase
    const loadNotes = async () => {
      try {
        const response = await fetch(`${API}/notes`);
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

    // Load notes initially
    loadNotes();

    // Set up polling to refresh notes every 30 seconds
    const intervalId = setInterval(loadNotes, 30000);

    return () => {
      unsubFolders();
      clearInterval(intervalId);
    };
  }, [userId, firestoreDb]);

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
      const response = await fetch(`${API}/notes`, {
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
      const response = await fetch(`${API}/notes/${noteId}`, {
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
      const response = await fetch(`${API}/notes/${noteId}`, {
        method: "DELETE",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to delete note");

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
      const response = await fetch(`${API}/notes/${noteId}/share`, {
        method: "POST",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to share note");

      const data = await response.json();
      const shareUrl = `${window.location.origin}/shared/${data.share_link}`;

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
      const response = await fetch(`${API}/folders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name, color })
      });

      if (!response.ok) throw new Error("Failed to create folder");
      toast.success("Folder created");
    } catch (error) {
      console.error("Create folder error:", error);
      toast.error("Failed to create folder");
    }
  };

  // Delete folder
  const handleDeleteFolder = async (folderId) => {
    try {
      const response = await fetch(`${API}/folders/${folderId}`, {
        method: "DELETE",
        credentials: "include"
      });

      if (!response.ok) throw new Error("Failed to delete folder");

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
      <div className="min-h-screen flex items-center justify-center bg-[#F4F0EB]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E06A4F] mx-auto"></div>
          <p className="mt-4 text-[#78716C] font-body">Loading your notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-[#F4F0EB]" data-testid="dashboard">
      {/* Desktop Sidebar */}
      <div className="hidden md:block w-72 flex-shrink-0 border-r border-[#E7E5E4]">
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

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-[#F4F0EB] border-b border-[#E7E5E4] px-4 py-3 flex items-center justify-between">
        <Sheet open={isMobileSidebarOpen} onOpenChange={setIsMobileSidebarOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" data-testid="mobile-menu-button">
              <Menu className="h-5 w-5 text-[#1C1917]" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 w-80 bg-[#F4F0EB]">
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
      <div className="flex-1 flex flex-col md:pt-0 pt-14">
        {selectedNote ? (
          <NoteEditor
            note={selectedNote}
            folders={folders}
            onUpdate={handleUpdateNote}
            onDelete={handleDeleteNote}
            onShare={handleShareNote}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <img
                src="https://images.unsplash.com/photo-1759296844873-e0c694c24284?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwzfHxtaW5pbWFsaXN0JTIwY2xlYW4lMjBkZXNrJTIwd29ya3NwYWNlJTIwYnJpZ2h0fGVufDB8fHx8MTc3NDUzNjU0MXww&ixlib=rb-4.1.0&q=85"
                alt="Empty state"
                className="w-48 h-48 object-cover rounded-2xl mx-auto mb-6 opacity-80"
              />
              <h2 className="font-heading text-2xl font-semibold text-[#1C1917] mb-2">
                No note selected
              </h2>
              <p className="text-[#78716C] font-body mb-6">
                Select a note from the sidebar or create a new one to get started
              </p>
              <Button
                onClick={handleCreateNote}
                className="bg-[#E06A4F] hover:bg-[#C95A41] text-white rounded-full px-6"
                data-testid="create-first-note-button"
              >
                <Plus className="h-4 w-4 mr-2" />
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
